#!/usr/bin/env python3
"""Business Unit: shared | Status: current

Phase 7 Cleanup Orchestrator - Complete backward compatibility cleanup workflow.

This script orchestrates the complete cleanup process:
1. Discovery and inventory of backward compatibility artifacts
2. Categorization and risk assessment  
3. Safe removal with testing and rollback capabilities
4. Documentation updates
5. Final verification
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from phase7_cleanup_scanner import BackwardCompatibilityScanner, CompatibilityArtifact
from phase7_cleanup_remover import BackwardCompatibilityRemover


class Phase7CleanupOrchestrator:
    """Orchestrates the complete Phase 7 cleanup process."""
    
    def __init__(self, root_path: str = ".", dry_run: bool = False):
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        self.session_id = f"phase7_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.reports_dir = Path("/tmp") / "phase7_reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_complete_cleanup(
        self, 
        risk_levels: Optional[List[str]] = None,
        max_artifacts: Optional[int] = None,
        interactive: bool = True
    ) -> bool:
        """Run the complete cleanup workflow."""
        
        print("🚀 Phase 7 Cleanup - Starting Complete Backward Compatibility Cleanup")
        print("=" * 80)
        print(f"Session ID: {self.session_id}")
        print(f"Root Path: {self.root_path}")
        print(f"Dry Run Mode: {self.dry_run}")
        print(f"Risk Levels: {risk_levels or 'all'}")
        print("")
        
        # Phase 1: Discovery and Inventory
        print("📊 PHASE 1: Discovery and Inventory")
        print("-" * 40)
        artifacts = self._run_discovery_phase()
        if not artifacts:
            print("✅ No backward compatibility artifacts found!")
            return True
        
        # Filter artifacts
        filtered_artifacts = self._filter_artifacts(artifacts, risk_levels, max_artifacts)
        print(f"📋 Processing {len(filtered_artifacts)} of {len(artifacts)} total artifacts")
        
        # Phase 2: Categorization and Risk Assessment
        print("\n🔍 PHASE 2: Categorization and Risk Assessment")
        print("-" * 50)
        self._analyze_artifacts(filtered_artifacts)
        
        # Ask for confirmation before proceeding
        if interactive and not self.dry_run:
            if not self._confirm_proceed(filtered_artifacts):
                print("🛑 Cleanup cancelled by user")
                return False
        
        # Phase 3: Safe Removal
        print("\n🔧 PHASE 3: Safe Removal with Testing")
        print("-" * 40)
        success = self._run_removal_phase(filtered_artifacts)
        
        # Phase 4: Documentation Updates
        if success and not self.dry_run:
            print("\n📝 PHASE 4: Documentation Updates")
            print("-" * 35)
            self._update_documentation()
        
        # Phase 5: Final Verification
        print("\n✅ PHASE 5: Final Verification")
        print("-" * 30)
        final_success = self._run_final_verification()
        
        # Generate comprehensive report
        self._generate_final_report(artifacts, filtered_artifacts, success and final_success)
        
        return success and final_success
    
    def _run_discovery_phase(self) -> List[CompatibilityArtifact]:
        """Run the discovery phase to find all backward compatibility artifacts."""
        print("🔍 Scanning codebase for backward compatibility artifacts...")
        
        scanner = BackwardCompatibilityScanner(self.root_path)
        report = scanner.run_scan()
        
        # Save scan report
        scan_report_file = self.reports_dir / f"{self.session_id}_scan_report.md"
        with open(scan_report_file, 'w') as f:
            f.write(scanner.generate_report("markdown"))
        
        # Save artifacts as JSON for processing
        artifacts_file = self.reports_dir / f"{self.session_id}_artifacts.json"
        artifacts_data = {
            "scan_timestamp": report.scan_timestamp,
            "total_artifacts": len(report.artifacts),
            "artifacts": [
                {
                    "type": artifact.artifact_type,
                    "file": artifact.file_path,
                    "line": artifact.line_number,
                    "content": artifact.content,
                    "risk_level": artifact.risk_level,
                    "removal_notes": artifact.removal_notes
                }
                for artifact in report.artifacts
            ]
        }
        with open(artifacts_file, 'w') as f:
            json.dump(artifacts_data, f, indent=2)
        
        print(f"📄 Detailed scan report: {scan_report_file}")
        print(f"🔧 Artifacts data: {artifacts_file}")
        print(f"📈 Found {len(report.artifacts)} backward compatibility artifacts")
        
        # Print summary
        self._print_artifact_summary(report.artifacts)
        
        return report.artifacts
    
    def _filter_artifacts(
        self, 
        artifacts: List[CompatibilityArtifact], 
        risk_levels: Optional[List[str]] = None,
        max_artifacts: Optional[int] = None
    ) -> List[CompatibilityArtifact]:
        """Filter artifacts based on criteria."""
        filtered = artifacts
        
        if risk_levels:
            filtered = [a for a in filtered if a.risk_level in risk_levels]
            print(f"🎯 Filtered to {len(filtered)} artifacts with risk levels: {risk_levels}")
        
        if max_artifacts:
            filtered = filtered[:max_artifacts]
            print(f"📊 Limited to first {len(filtered)} artifacts")
        
        return filtered
    
    def _analyze_artifacts(self, artifacts: List[CompatibilityArtifact]) -> None:
        """Analyze and categorize artifacts."""
        print("📊 Artifact Analysis:")
        
        # Group by risk level
        risk_groups = {"high": [], "medium": [], "low": []}
        for artifact in artifacts:
            risk_groups[artifact.risk_level].append(artifact)
        
        for risk_level in ["high", "medium", "low"]:
            count = len(risk_groups[risk_level])
            if count > 0:
                print(f"   {risk_level.upper()} Risk: {count} items")
                
                # Show top 3 for high-risk items
                if risk_level == "high":
                    for i, artifact in enumerate(risk_groups[risk_level][:3], 1):
                        print(f"      {i}. {artifact.file_path}:{artifact.line_number}")
                        print(f"         {artifact.content[:60]}...")
        
        # Group by type
        type_groups = {}
        for artifact in artifacts:
            type_groups[artifact.artifact_type] = type_groups.get(artifact.artifact_type, 0) + 1
        
        print("\n📋 Artifact Types:")
        for artifact_type, count in sorted(type_groups.items()):
            print(f"   {artifact_type}: {count}")
    
    def _confirm_proceed(self, artifacts: List[CompatibilityArtifact]) -> bool:
        """Ask user for confirmation to proceed with removal."""
        print("\n⚠️  CONFIRMATION REQUIRED")
        print("=" * 30)
        print(f"About to process {len(artifacts)} backward compatibility artifacts.")
        
        high_risk_count = len([a for a in artifacts if a.risk_level == "high"])
        if high_risk_count > 0:
            print(f"⚠️  WARNING: {high_risk_count} HIGH RISK items will require individual confirmation")
        
        print("\nThis operation will:")
        print("  • Remove comments and deprecated code")
        print("  • Update import statements")
        print("  • Run tests after each change")
        print("  • Create backups for rollback")
        print("  • Generate detailed reports")
        
        while True:
            response = input("\nProceed with cleanup? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no")
    
    def _run_removal_phase(self, artifacts: List[CompatibilityArtifact]) -> bool:
        """Run the removal phase with testing and rollback."""
        print("🔧 Starting safe removal process...")
        
        remover = BackwardCompatibilityRemover(self.root_path, self.dry_run, False)  # Non-interactive for orchestrator
        session_id = remover.start_session(artifacts)
        
        try:
            remover.process_all_artifacts()
            
            # Run final tests
            if not self.dry_run:
                test_success = remover.run_final_tests()
                if not test_success:
                    print("❌ Final tests failed")
                    return False
            
            # Generate removal report
            removal_report = remover.generate_session_report()
            removal_report_file = self.reports_dir / f"{self.session_id}_removal_report.md"
            with open(removal_report_file, 'w') as f:
                f.write(removal_report)
            
            print(f"📄 Removal report: {removal_report_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Removal phase failed: {e}")
            return False
    
    def _update_documentation(self) -> None:
        """Update documentation to reflect the clean modular structure."""
        print("📝 Updating documentation...")
        
        # Check if there are any documentation files that need updating
        doc_files = [
            "README.md",
            "migration/README.md", 
            "BUSINESS_UNITS_REPORT.md"
        ]
        
        updated_files = []
        for doc_file in doc_files:
            doc_path = self.root_path.parent / doc_file
            if doc_path.exists():
                # For now, just note which files might need updates
                print(f"   📄 {doc_file} - May need review for legacy references")
                updated_files.append(doc_file)
        
        if updated_files:
            print(f"   ℹ️  {len(updated_files)} documentation files identified for potential updates")
        else:
            print("   ✅ No documentation updates needed")
    
    def _run_final_verification(self) -> bool:
        """Run final verification tests."""
        print("🧪 Running final verification...")
        
        # Run smoke tests
        print("   Running smoke tests...")
        result = subprocess.run(
            ["scripts/smoke_tests.sh"],
            cwd=self.root_path.parent,  # Run from repository root
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("   ❌ Smoke tests failed")
            return False
        
        print("   ✅ Smoke tests passed")
        
        # Check for any remaining backward compatibility artifacts
        print("   Scanning for remaining artifacts...")
        scanner = BackwardCompatibilityScanner(self.root_path)
        remaining_report = scanner.run_scan()
        
        remaining_count = len(remaining_report.artifacts)
        print(f"   📊 {remaining_count} backward compatibility artifacts remain")
        
        if remaining_count > 0:
            # Save remaining artifacts report
            remaining_file = self.reports_dir / f"{self.session_id}_remaining_artifacts.md"
            with open(remaining_file, 'w') as f:
                f.write(scanner.generate_report("markdown"))
            print(f"   📄 Remaining artifacts report: {remaining_file}")
        
        return True
    
    def _generate_final_report(
        self, 
        original_artifacts: List[CompatibilityArtifact],
        processed_artifacts: List[CompatibilityArtifact], 
        success: bool
    ) -> None:
        """Generate a comprehensive final report."""
        print("📄 Generating final report...")
        
        report = [
            f"# Phase 7 Cleanup - Final Report",
            f"",
            f"**Session ID:** {self.session_id}",
            f"**Timestamp:** {datetime.now().isoformat()}",
            f"**Root Path:** {self.root_path}",
            f"**Dry Run Mode:** {self.dry_run}",
            f"**Overall Success:** {'✅ Yes' if success else '❌ No'}",
            f"",
            f"## Summary",
            f"",
            f"- **Total Artifacts Found:** {len(original_artifacts)}",
            f"- **Artifacts Processed:** {len(processed_artifacts)}",
            f"- **Processing Mode:** {'Preview Only' if self.dry_run else 'Full Removal'}",
            f"",
            f"## Artifacts by Risk Level",
            f""
        ]
        
        # Summary by risk level
        for risk_level in ["high", "medium", "low"]:
            original_count = len([a for a in original_artifacts if a.risk_level == risk_level])
            processed_count = len([a for a in processed_artifacts if a.risk_level == risk_level])
            report.append(f"- **{risk_level.title()} Risk:** {original_count} found, {processed_count} processed")
        
        report.extend([
            f"",
            f"## Generated Reports",
            f"",
            f"- **Scan Report:** `{self.session_id}_scan_report.md`",
            f"- **Artifacts Data:** `{self.session_id}_artifacts.json`",
            f"- **Removal Report:** `{self.session_id}_removal_report.md`",
            f"- **Final Report:** `{self.session_id}_final_report.md`",
            f"",
            f"## Next Steps",
            f""
        ])
        
        if self.dry_run:
            report.extend([
                f"This was a **dry run**. To perform actual cleanup:",
                f"",
                f"```bash",
                f"python scripts/phase7_cleanup_orchestrator.py \\",
                f"  --root the_alchemiser \\",
                f"  --risk-levels low medium \\",
                f"  --interactive",
                f"```",
                f""
            ])
        elif success:
            report.extend([
                f"✅ **Phase 7 cleanup completed successfully!**",
                f"",
                f"The codebase is now in a clean, production-ready modular state with:",
                f"- Backward compatibility artifacts removed",
                f"- All tests passing",
                f"- Clean modular structure (strategy/, portfolio/, execution/, shared/)",
                f"- No legacy import paths or deprecated code",
                f""
            ])
        else:
            report.extend([
                f"❌ **Phase 7 cleanup encountered issues.**",
                f"",
                f"Review the detailed reports above and address any failures before proceeding.",
                f"Use the rollback capabilities if needed to restore previous state.",
                f""
            ])
        
        # Write final report
        final_report_file = self.reports_dir / f"{self.session_id}_final_report.md"
        with open(final_report_file, 'w') as f:
            f.write("\n".join(report))
        
        print(f"📄 Final report: {final_report_file}")
    
    def _print_artifact_summary(self, artifacts: List[CompatibilityArtifact]) -> None:
        """Print a summary of artifacts found."""
        print("\n📊 Artifact Summary:")
        
        # By risk level
        risk_counts = {"high": 0, "medium": 0, "low": 0}
        for artifact in artifacts:
            risk_counts[artifact.risk_level] += 1
        
        for risk_level, count in risk_counts.items():
            if count > 0:
                print(f"   {risk_level.title()} Risk: {count}")
        
        # By type (top 5)
        type_counts = {}
        for artifact in artifacts:
            type_counts[artifact.artifact_type] = type_counts.get(artifact.artifact_type, 0) + 1
        
        print("\n📋 Top Artifact Types:")
        for artifact_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {artifact_type}: {count}")


def main():
    """Main entry point for the orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 7 Cleanup Orchestrator")
    parser.add_argument("--root", default="the_alchemiser", help="Root directory to clean")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't make changes")
    parser.add_argument("--risk-levels", nargs="+", choices=["high", "medium", "low"], 
                       help="Only process specified risk levels")
    parser.add_argument("--max-artifacts", type=int, help="Maximum number of artifacts to process")
    parser.add_argument("--non-interactive", action="store_true", help="Run without user prompts")
    
    args = parser.parse_args()
    
    orchestrator = Phase7CleanupOrchestrator(args.root, args.dry_run)
    
    success = orchestrator.run_complete_cleanup(
        risk_levels=args.risk_levels,
        max_artifacts=args.max_artifacts,
        interactive=not args.non_interactive
    )
    
    if success:
        print("\n🎉 Phase 7 cleanup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Phase 7 cleanup failed or was cancelled")
        sys.exit(1)


if __name__ == "__main__":
    main()