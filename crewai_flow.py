"""CrewAI Flow for the fixed equity-research desk process.

The graph, not an LLM, fixes the normal execution order.  The Strategy
Manager can request at most one deterministic, code-selected revision before
the Verifier always runs.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from crewai.flow import Flow, listen, start
from pydantic import BaseModel, Field

from desk import (
    Filing,
    extract_10k_excerpts,
    extract_release_excerpts,
    format_millions,
    get_model_client,
    verified_financial_claims,
    write_json,
)
from verifier_agent import (
    VerificationResult,
    audit_saved_run,
    cited_filing_texts,
    marks_from_model,
    render_verified_report,
)
from insight_checks import (
    final_insight_line,
    insight_lines,
    release_first_paragraph,
    valid_final_insight,
    without_final_insight,
)


REQUIRED_REPORT_SECTIONS = (
    "## 1. Overview",
    "## 2. Market Positioning and Growth Outlook",
    "## 3. Valuation Insights",
    "## 4. Future Developments and Strategic Recommendations",
    "## 5. Investment Recommendation",
)


class EquityResearchState(BaseModel):
    """Typed state shared by every Flow node."""

    ticker: str = ""
    peers: str = ""
    price: float | None = None
    output_root: str = "outputs"
    run_folder: str = ""
    model: str = ""
    research_output: str = ""
    financial_output: str = ""
    advisor_output: str = ""
    manager_output: str = ""
    report_path: str = ""
    verifier_path: str = ""
    revision_role: str = ""
    manager_status: str = ""
    node_order: list[str] = Field(default_factory=list)


class EquityResearchFlow(Flow[EquityResearchState]):
    """Fixed CrewAI process: steps -> three specialists -> manager -> verifier."""

    @staticmethod
    def _instructions(role: str) -> str:
        path = Path(__file__).with_name("roles") / f"{role}.md"
        return path.read_text(encoding="utf-8")

    def _folder(self) -> Path:
        folder = Path(self.state.run_folder)
        if not folder.is_dir():
            raise FileNotFoundError(f"Saved run folder does not exist: {folder}")
        return folder

    def _artifacts(self) -> dict[str, Any]:
        folder = self._folder()
        metadata = json.loads((folder / "run_metadata.json").read_text(encoding="utf-8"))
        return {
            "metadata": metadata,
            "filings": {name: Filing(**value) for name, value in metadata["filings"].items()},
            "facts": json.loads((folder / "facts.json").read_text(encoding="utf-8")),
            "ratios": json.loads((folder / "ratios.json").read_text(encoding="utf-8")),
            "evidence": json.loads((folder / "release_evidence.json").read_text(encoding="utf-8")),
            "peers": json.loads((folder / "peers.json").read_text(encoding="utf-8")),
        }

    def _record(self, node: str, input_value: Any, output_value: Any) -> None:
        folder = self._folder()
        artifact_folder = folder / "flow_artifacts"
        artifact_folder.mkdir(exist_ok=True)
        write_json(artifact_folder / f"{len(self.state.node_order):02d}_{node}_input.json", input_value)
        if isinstance(output_value, str):
            (artifact_folder / f"{len(self.state.node_order):02d}_{node}_output.md").write_text(
                output_value.rstrip() + "\n", encoding="utf-8"
            )
        else:
            write_json(artifact_folder / f"{len(self.state.node_order):02d}_{node}_output.json", output_value)
        self.state.node_order.append(node)

    def _chat(
        self,
        system: str,
        payload: dict[str, Any],
        *,
        max_tokens: int,
        temperature: float = 0.2,
        json_output: bool = False,
    ) -> str:
        client, configured_model = get_model_client(Path(__file__).with_name(".env"))
        model = self.state.model or configured_model
        self.state.model = model
        options: dict[str, Any] = {}
        if json_output:
            options["response_format"] = {"type": "json_object"}
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            **options,
        )
        return response.choices[0].message.content or ""

    @start()
    def steps(self) -> str:
        """Run the seven filing-first tools or validate a supplied saved run."""
        print("Node: steps", flush=True)
        if not self.state.run_folder:
            if not self.state.ticker:
                raise ValueError("A ticker is required for a full run.")
            command = [
                sys.executable,
                str(Path(__file__).with_name("desk.py")),
                self.state.ticker.upper(),
                "--output-root",
                self.state.output_root,
                "--no-roles",
            ]
            if self.state.peers:
                command.extend(["--peers", self.state.peers])
            if self.state.price is not None:
                command.extend(["--price", str(self.state.price)])
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
            marker = "Saved run folder: "
            saved_lines = [line for line in completed.stdout.splitlines() if line.startswith(marker)]
            if not saved_lines:
                raise RuntimeError("The seven steps did not report a saved run folder.")
            self.state.run_folder = saved_lines[-1][len(marker) :].strip()
        required = (
            "run_metadata.json",
            "facts.json",
            "ratios.json",
            "release_evidence.json",
            "peers.json",
            "latest_10-K.txt",
            "earnings_release_EX-99.1.txt",
        )
        missing = [name for name in required if not (self._folder() / name).exists()]
        if missing:
            raise FileNotFoundError("The seven desk steps are incomplete: " + ", ".join(missing))
        data = self._artifacts()
        write_json(
            self._folder() / "saved_facts.json",
            {
                "facts": data["facts"],
                "calculated_ratios": data["ratios"],
                "quarter_evidence": data["evidence"],
                "peer_facts": data["peers"],
            },
        )
        output = "Seven saved data steps are ready."
        self._record(
            "steps",
            {
                "ticker": self.state.ticker,
                "peers": self.state.peers,
                "price": self.state.price,
            },
            {"status": output, "run_folder": self.state.run_folder},
        )
        return output

    @listen(steps)
    def research_analyst(self) -> str:
        print("Node: Research Analyst", flush=True)
        folder = self._folder()
        payload = {
            "task": (
                "Analyze the business model, competition, catalysts, and recent developments. "
                "Cite a saved filing line for every claim. End with one Insight line that states "
                "a sourced numeric claim that the release's first paragraph does not state."
            ),
            "context": {
                "10-K_excerpts": extract_10k_excerpts((folder / "latest_10-K.txt").read_text(encoding="utf-8")),
                "earnings_release_excerpts": extract_release_excerpts(
                    (folder / "earnings_release_EX-99.1.txt").read_text(encoding="utf-8")
                ),
            },
            "expected_output": (
                "Markdown with the three required headings. The last nonblank line must start with "
                "Insight: and contain one number plus its saved filing-line citation."
            ),
        }
        self.state.research_output = self._chat(
            self._instructions("research_analyst"), payload, max_tokens=1400
        )
        self._record("research_analyst", payload, self.state.research_output)
        return self.state.research_output

    def _financial_payload(self) -> tuple[dict[str, Any], str, list[str]]:
        data = self._artifacts()
        verified = verified_financial_claims(
            data["filings"], data["facts"], data["ratios"], data["evidence"], data["peers"]
        )
        payload = {
            "task": "Analyze the saved statements and ratios. Copy the code-verified block without changing or recalculating a value.",
            "context": {
                "source_filings": {name: asdict(filing) for name, filing in data["filings"].items()},
                "verified_claims_from_calculator": verified,
                "step_4_facts": data["facts"],
                "step_5_ratios": data["ratios"],
                "step_6_quarter_evidence": data["evidence"],
                "step_7_peers": data["peers"],
            },
            "expected_output": (
                "Markdown with statement, valuation, quarter, and peer sections plus all 11 verified claims. "
                "End with one Insight line that includes a number and its saved filing-line citation."
            ),
        }
        facts, ratios, evidence = data["facts"], data["ratios"], data["evidence"]
        tokens = [
            f"${format_millions(facts['total_revenue']['value'])} million",
            f"{ratios['operating_margin']['value'] * 100:.4f}%",
            f"${float(facts['diluted_eps']['value']):.2f}",
            f"${float(evidence['quarter_total_revenue']):,.0f} million",
            f"${float(evidence['quarter_diluted_eps']):.2f}",
        ]
        return payload, verified, tokens

    @listen(research_analyst)
    def financial_analyst(self) -> str:
        print("Node: Financial Analyst", flush=True)
        payload, verified, tokens = self._financial_payload()
        output = self._chat(self._instructions("financial_analyst"), payload, max_tokens=2400)
        self.state.financial_output = output if all(token in output for token in tokens) else verified
        self._record("financial_analyst", payload, self.state.financial_output)
        return self.state.financial_output

    @listen(financial_analyst)
    def investment_advisor(self) -> str:
        print("Node: Investment Advisor", flush=True)
        payload = {
            "task": (
                "Synthesize the two analyst outputs into a Buy, Hold, or Sell thesis and state one deciding number. "
                "End with one Insight line that states a sourced numeric claim that the release's first paragraph "
                "does not state."
            ),
            "context": {
                "research_analyst_output": self.state.research_output,
                "financial_analyst_output": self.state.financial_output,
            },
            "expected_output": (
                "Markdown with Investment Thesis, Recommendation, and The Deciding Number. The last nonblank "
                "line must start with Insight: and contain one number plus its saved filing-line citation."
            ),
        }
        self.state.advisor_output = self._chat(
            self._instructions("investment_advisor"), payload, max_tokens=1000
        )
        self._record("investment_advisor", payload, self.state.advisor_output)
        return self.state.advisor_output

    def _part_checks(self) -> dict[str, bool]:
        has_citation = "[10-K Line" in self.state.research_output or "[EX-99.1 Line" in self.state.research_output
        _, _, financial_tokens = self._financial_payload()
        advisor_lower = self.state.advisor_output.lower()
        release_text = (self._folder() / "earnings_release_EX-99.1.txt").read_text(encoding="utf-8")
        first_paragraph = release_first_paragraph(release_text)
        research_insight = valid_final_insight(self.state.research_output, first_paragraph)
        financial_insight = valid_final_insight(self.state.financial_output, first_paragraph)
        advisor_insight = valid_final_insight(self.state.advisor_output, first_paragraph)
        return {
            "Overview": (
                "### Business Model and Operations" in self.state.research_output
                and has_citation
                and research_insight
            ),
            "Market Positioning and Growth Outlook": (
                "### Competitive Position and Moat" in self.state.research_output
                and has_citation
                and research_insight
            ),
            "Valuation Insights": (
                all(token in self.state.financial_output for token in financial_tokens)
                and financial_insight
            ),
            "Future Developments and Strategic Recommendations": (
                "### Catalysts and Recent Developments" in self.state.research_output
                and has_citation
                and research_insight
            ),
            "Investment Recommendation": (
                all(
                    heading in self.state.advisor_output
                    for heading in ("### Investment Thesis", "### Recommendation", "### The Deciding Number")
                )
                and any(word in advisor_lower for word in ("buy", "hold", "sell"))
                and any(token in self.state.advisor_output for token in financial_tokens)
                and advisor_insight
            ),
        }

    def _revision_target(self, part_checks: dict[str, bool]) -> Literal["Research Analyst", "Financial Analyst", "Investment Advisor", ""]:
        failed = next((part for part, passed in part_checks.items() if not passed), "")
        if failed in {
            "Overview",
            "Market Positioning and Growth Outlook",
            "Future Developments and Strategic Recommendations",
        }:
            return "Research Analyst"
        if failed == "Valuation Insights":
            return "Financial Analyst"
        if failed == "Investment Recommendation":
            return "Investment Advisor"
        return ""

    @listen(investment_advisor)
    def strategy_manager(self) -> str:
        print("Node: Strategy Manager", flush=True)
        part_checks = self._part_checks()
        target = self._revision_target(part_checks)
        self.state.revision_role = target
        if target == "Research Analyst":
            print("Node: Research Analyst (revision 2 of 2)", flush=True)
            folder = self._folder()
            payload = {
                "task": (
                    "One allowed revision: restore every required heading and add a saved filing-line citation to "
                    "every claim. End with one Insight line. It must contain a sourced number that the earnings "
                    "release's first paragraph does not state."
                ),
                "context": {
                    "previous_draft": self.state.research_output,
                    "10-K_excerpts": extract_10k_excerpts((folder / "latest_10-K.txt").read_text(encoding="utf-8")),
                },
                "expected_output": "A corrected Research Analyst draft that ends with one valid Insight line.",
            }
            self.state.research_output = self._chat(
                self._instructions("research_analyst"), payload, max_tokens=1600, temperature=0.1
            )
            self._record("research_analyst_revision", payload, self.state.research_output)
        elif target == "Financial Analyst":
            print("Node: Financial Analyst (revision 2 of 2)", flush=True)
            payload, verified, _ = self._financial_payload()
            payload["task"] = (
                "One allowed revision: copy the verified claims exactly and do not recalculate them. End with one "
                "Insight line. It must contain a sourced number that the release's first paragraph does not state."
            )
            revised = self._chat(
                self._instructions("financial_analyst"), payload, max_tokens=2600, temperature=0
            )
            self.state.financial_output = revised or verified
            self._record("financial_analyst_revision", payload, self.state.financial_output)
        elif target == "Investment Advisor":
            print("Node: Investment Advisor (revision 2 of 2)", flush=True)
            payload = {
                "task": (
                    "One allowed revision: include all three required headings, Buy/Hold/Sell, and one deciding "
                    "number. End with one Insight line. It must contain a sourced number that the earnings "
                    "release's first paragraph does not state."
                ),
                "context": {
                    "research_analyst_output": self.state.research_output,
                    "financial_analyst_output": self.state.financial_output,
                    "previous_draft": self.state.advisor_output,
                },
                "expected_output": "A corrected Investment Advisor draft that ends with one valid Insight line.",
            }
            self.state.advisor_output = self._chat(
                self._instructions("investment_advisor"), payload, max_tokens=1200, temperature=0.1
            )
            self._record("investment_advisor_revision", payload, self.state.advisor_output)

        part_checks = self._part_checks()
        manager_payload = {
            "task": "Compile the supplied work into the five required report parts. Return JSON with report_markdown. Do not choose the next role; code has already handled the single revision slot.",
            "context": {
                "research_analyst_output": self.state.research_output,
                "financial_analyst_output": self.state.financial_output,
                "investment_advisor_output": self.state.advisor_output,
            },
            "expected_output": {"format": "JSON", "required_report_headings": REQUIRED_REPORT_SECTIONS},
        }
        raw = self._chat(
            self._instructions("strategy_manager"),
            manager_payload,
            max_tokens=3200,
            temperature=0.1,
            json_output=True,
        )
        try:
            report = str(json.loads(raw).get("report_markdown", "")).strip()
        except json.JSONDecodeError:
            report = ""
        _, _, financial_tokens = self._financial_payload()
        expected_insights = [
            final_insight_line(self.state.research_output),
            final_insight_line(self.state.financial_output),
            final_insight_line(self.state.advisor_output),
        ]

        def compiled_report_is_complete(candidate: str) -> bool:
            compiled_insights = insight_lines(candidate)
            return (
                all(section in candidate for section in REQUIRED_REPORT_SECTIONS)
                and all(token in candidate for token in financial_tokens)
                and ("[10-K Line" in candidate or "[EX-99.1 Line" in candidate)
                and any(word in candidate.lower() for word in ("buy", "hold", "sell"))
                and len(compiled_insights) == 3
                and len(set(expected_insights)) == 3
                and sorted(compiled_insights) == sorted(expected_insights)
            )

        report_is_complete = compiled_report_is_complete(report)
        if not report_is_complete:
            research_without_insight = without_final_insight(self.state.research_output)
            report = (
                f"## 1. Overview\n\n{research_without_insight}\n\n"
                f"## 2. Market Positioning and Growth Outlook\n\n{research_without_insight}\n\n"
                f"## 3. Valuation Insights\n\n{self.state.financial_output}\n\n"
                f"## 4. Future Developments and Strategic Recommendations\n\n{self.state.research_output}\n\n"
                f"## 5. Investment Recommendation\n\n{self.state.advisor_output}"
            )
        manager_status = (
            "PASS" if all(part_checks.values()) and compiled_report_is_complete(report) else "FAIL_UNRESOLVED"
        )
        self.state.manager_status = manager_status
        data = self._artifacts()
        filings = data["filings"]
        run_time = data["metadata"].get("run_time", datetime.now().astimezone().isoformat())
        header = (
            f"# Filings Read: 10-K (accession: {filings['10-K'].accession}), "
            f"10-Q (accession: {filings['10-Q'].accession}), "
            f"8-K (accession: {filings['earnings_8-K'].accession})\n"
            f"Run Time: {run_time}\n"
            f"Manager Status: {manager_status}\n\n"
        )
        report_path = self._folder() / "report.md"
        report_path.write_text(header + report.rstrip() + "\n", encoding="utf-8")
        self.state.manager_output = report
        self.state.report_path = str(report_path)
        self._record(
            "strategy_manager",
            manager_payload,
            {
                "status": manager_status,
                "part_checks": part_checks,
                "revision_role": target,
                "report_markdown": report,
            },
        )
        return report

    @listen(strategy_manager)
    def verifier(self) -> dict[str, Any]:
        print("Node: Verifier", flush=True)
        folder = self._folder()
        report_path = Path(self.state.report_path) if self.state.report_path else folder / "report.md"
        deterministic = audit_saved_run(folder, report_path)
        saved_facts_path = folder / "saved_facts.json"
        if not saved_facts_path.exists():
            data = self._artifacts()
            write_json(
                saved_facts_path,
                {
                    "facts": data["facts"],
                    "calculated_ratios": data["ratios"],
                    "quarter_evidence": data["evidence"],
                    "peer_facts": data["peers"],
                },
            )
        payload = {
            "task": (
                "Check whether each cited line states the reported number for the stated period and definition. "
                "Skip the Investment Advisor thesis. Return JSON with semantic_marks."
            ),
            "context": {
                "compiled_report": report_path.read_text(encoding="utf-8"),
                "saved_filing_texts": cited_filing_texts(
                    report_path.read_text(encoding="utf-8"), folder
                ),
                "saved_facts": json.loads(saved_facts_path.read_text(encoding="utf-8")),
            },
            "expected_output": {
                "format": "JSON",
                "schema": {
                    "semantic_marks": [
                        {
                            "claim": "text",
                            "mark": "correct | wrong | unsupported",
                            "explanation": "text",
                            "correction": "text or empty",
                            "source": "real filing line or XBRL tag and period",
                        }
                    ]
                },
            },
        }
        raw_model_review = self._chat(
            self._instructions("verifier"), payload, max_tokens=2400, temperature=0, json_output=True
        )
        semantic_marks = marks_from_model(raw_model_review)
        marks = deterministic.marks + semantic_marks
        result = VerificationResult(
            verified=bool(marks) and all(mark.mark == "correct" for mark in marks),
            marks=marks,
        )
        output = result.to_dict()
        output["model_review"] = raw_model_review
        path = folder / "verification.json"
        verified_report_path = folder / "verified_report.md"
        output["run_folder"] = str(folder)
        output["verification_path"] = str(path)
        output["verified_report_path"] = str(verified_report_path)
        output["node_order"] = list(self.state.node_order) + ["verifier"]
        write_json(path, output)
        verified_report_path.write_text(
            render_verified_report(report_path.read_text(encoding="utf-8"), result),
            encoding="utf-8",
        )
        self.state.verifier_path = str(path)
        self._record("verifier", payload, output)
        return output


def run_flow(
    ticker: str,
    peers: str = "",
    price: float | None = None,
    output_root: str = "outputs",
    model: str = "",
) -> dict[str, Any]:
    flow = EquityResearchFlow()
    result = flow.kickoff(
        inputs={
            "ticker": ticker,
            "peers": peers,
            "price": price,
            "output_root": output_root,
            "model": model,
        }
    )
    return result if isinstance(result, dict) else {"result": str(result)}


def run_verifier_only(run_folder: Path, model: str = "") -> dict[str, Any]:
    """Run the same final Verifier node without starting any earlier node."""
    flow = EquityResearchFlow()
    flow.state.run_folder = str(run_folder)
    flow.state.report_path = str(run_folder / "report.md")
    flow.state.model = model
    return flow.verifier()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", nargs="?", help="Ticker for a full agent-team run")
    parser.add_argument("--peers", default="", help="Comma-separated peer tickers")
    parser.add_argument("--price", type=float, help="Dated share price for P/E")
    parser.add_argument("--output-root", default="outputs")
    parser.add_argument("--model", default="")
    parser.add_argument("--verify-only", type=Path, metavar="RUN_FOLDER")
    args = parser.parse_args()
    if args.verify_only:
        output = run_verifier_only(args.verify_only, args.model)
    else:
        if not args.ticker:
            parser.error("ticker is required unless --verify-only is used")
        output = run_flow(args.ticker, args.peers, args.price, args.output_root, args.model)
    print(json.dumps(output, indent=2))
    return 0 if output.get("verified", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
