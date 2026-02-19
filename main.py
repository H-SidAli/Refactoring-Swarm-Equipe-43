import argparse
import sys
import os
from dotenv import load_dotenv
from src.utils.logger import log_experiment, ActionType
from src.swarm import RefactoringSwarm

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Refactoring Swarm - Automated Python code analysis and refactoring"
    )
    parser.add_argument("--target_dir", type=str, required=True, help="Directory containing Python files to refactor")
    parser.add_argument("--model", type=str, default="mistral-small-latest", help="LLM model to use")
    parser.add_argument("--dry-run", action="store_true", help="Only scan and audit, skip fixes")
    args = parser.parse_args()

    if not os.path.exists(args.target_dir):
        print(f"❌ Dossier {args.target_dir} introuvable.")
        sys.exit(1)

    print(f"🚀 DEMARRAGE SUR : {args.target_dir}")
    log_experiment(
        agent_name="System",
        model_used="N/A",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": f"Startup initialization for target directory: {args.target_dir}",
            "output_response": "System ready - awaiting agent execution"
        },
        status="SUCCESS"
    )

    # Initialize and run the swarm
    try:
        swarm = RefactoringSwarm(model_name=args.model)
        result = swarm.run(args.target_dir)
        
        if result["errors"]:
            print(f"\n⚠️ Terminé avec {len(result['errors'])} erreur(s)")
            sys.exit(1)
        else:
            print("\n✅ MISSION_COMPLETE")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        log_experiment(
            agent_name="System",
            model_used="N/A",
            action=ActionType.DEBUG,
            details={
                "input_prompt": f"Fatal error during swarm execution",
                "output_response": str(e)
            },
            status="FAILURE"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()