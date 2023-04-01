import subprocess
from typing import List

import rich
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from kopylot.audit import run_audit
from kopylot.diagnose import run_diagnose
from kopylot.utils import ai_print

app = typer.Typer()
console = Console()


@app.command()
def ctl(args: List[str]) -> subprocess.CompletedProcess:
    """
    A wrapper around kubectl. The arguments passed to the ctl subcommand are interpreted by kubectl.
    """
    kubectl_args = " ".join(args)
    kubectl_command = f"kubectl {kubectl_args}"
    return subprocess.run(kubectl_command, shell=True)


@app.command()
def diagnose(
    resource_type: str = typer.Argument(..., help="The type of resource to diagnose. E.g.: pod, deployment, service"),
    resource_name: str = typer.Argument(..., help="The name of the resource to diagnose"),
    show_describe: bool = typer.Option(False, "--show-describe", help="Show the output of `kubectl describe`"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output and borders"),
) -> str:
    """
    Diagnose a pod, deployment, or service using an LLM model.
    """
    # run `kubectl describe` for the resource
    describe_command = f"kubectl describe {resource_type} {resource_name}"

    with console.status("[bold green]Getting resource description..."):
        describe_result = subprocess.run(describe_command, shell=True, capture_output=True)

    describe_decoded_result = describe_result.stdout.decode("utf-8")
    if show_describe:
        if no_color:
            print(describe_decoded_result)
        else:
            rich.print(Panel(Text(describe_decoded_result), title=f"{resource_type.title()} description"))

    with console.status("[bold green]Running diagnosis..."):
        diagnose_result: str = run_diagnose(resource_type, describe_decoded_result)
    ai_print(f"Diagnosis for the {resource_type.title()} {resource_name}", diagnose_result, no_color)

    return diagnose_result


@app.command()
def audit(
    resource_type: str = typer.Argument(..., help="The type of resource to audit. E.g: pod, deployment, service"),
    resource_name: str = typer.Argument(..., help="The name of the resource to audit"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output and borders"),
) -> str:
    """
    Audit a pod, deployment, or service using an LLM model.
    """
    # run `kubectl get {resource_type} {resource_name} -oyaml` to get the resource's yaml
    get_yaml_command = f"kubectl get {resource_type} {resource_name} -oyaml"

    with console.status("[bold green]Getting resource yaml..."):
        get_yaml_restult = subprocess.run(get_yaml_command, shell=True, capture_output=True)

    get_yaml_result_decoded = get_yaml_restult.stdout.decode("utf-8")

    with console.status("[bold green]Running audit..."):
        audit_result: str = run_audit(resource_type, get_yaml_result_decoded)
    ai_print(f"Audit for the {resource_type.title()} {resource_name}", audit_result, no_color, style="bold red")

    return audit_result


if __name__ == "__main__":
    app()
