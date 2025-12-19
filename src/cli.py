import typer
from typing_extensions import Annotated
import pandas as pd
import os
import time
import tomllib
from infra.adapters.excel_reader_adapter import ExcelReaderAdapter
from infra.adapters.bandtrass_scraper_adapter import BandtrassScraperAdapter
from domain.services.data_processor import DataProcessor

app = typer.Typer(no_args_is_help=True)

import glob

def _get_latest_data_file(directory: str = "data") -> str:
    """
    Finds the latest .xlsx file in the specified directory.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    files = glob.glob(os.path.join(directory, "*.xlsx"))
    if not files:
        raise FileNotFoundError(f"No .xlsx files found in {directory}")
        
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def _generate_report(input_file: str, start_year: int, end_year: int, output: str):
    """
    Internal function to generate the report.
    Returns the output path on success.
    """
    if input_file is None:
        try:
            input_file = _get_latest_data_file()
            typer.echo(f"Auto-detected latest input file: {input_file}")
        except Exception as e:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    typer.echo(f"Generating report from {input_file}...")
    typer.echo(f"Filtering range: {start_year} ~ {end_year}")
    
    try:
        # 1. Read
        adapter = ExcelReaderAdapter()
        raw_df = adapter.read(input_file)
        
        # 2. Process Monthly
        processor = DataProcessor()
        monthly_df_all = processor.process(raw_df)
        
        # 3. Process Quarterly
        quarterly_df_all = processor.process_quarterly(monthly_df_all)
        
        # 4. Filter
        monthly_df_filtered = processor.filter_by_year(monthly_df_all, start_year, end_year)
        quarterly_df_filtered = processor.filter_quarterly_by_year(quarterly_df_all, start_year, end_year)
        
        typer.echo(f"Exporting {len(monthly_df_filtered)} monthly records and {len(quarterly_df_filtered)} quarterly records.")
        
        # 5. Export
        output_dir = os.path.dirname(output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            monthly_df_filtered.to_excel(writer, sheet_name='Monthly', index=False)
            quarterly_df_filtered.to_excel(writer, sheet_name='Quarterly', index=False)
            
        typer.echo(f"Successfully generated report at {output}")
        return output

    except Exception as e:
        typer.secho(f"Error generating report: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

def _download_data(output_dir: str, headless: bool = True, strategy_name: str = None) -> str:
    """
    Internal function to run the scraper and download data.
    Returns the path to the downloaded (converted) file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    strategy_config = None
    if strategy_name:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        strategy_file = os.path.join(project_root, "strategies", f"{strategy_name}.toml")
        if os.path.exists(strategy_file):
            typer.echo(f"[Strategy] Loading strategy from: {strategy_file}")
            with open(strategy_file, "rb") as f:
                strategy_config = tomllib.load(f)
            typer.echo(f"[Strategy] Loaded configuration for: {strategy_config.get('name', 'Unknown')}")
        else:
            typer.secho(f"[Error] Strategy file not found: {strategy_file}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    typer.echo(f"Starting download to {output_dir}...")
    scraper = BandtrassScraperAdapter(headless=headless)
    try:
        file_path = scraper.download_data(output_dir, strategy=strategy_config)
        typer.echo(f"Download completed: {file_path}")
        return file_path
    except Exception as e:
        typer.secho(f"Error downloading data: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def download(
    output_dir: str = typer.Option("data", "--output-dir", help="Directory to save downloaded data"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
    strategy: str = typer.Option(None, "--strategy", help="Name of the strategy to use (e.g., 'HD현대일렉트릭')")
):
    """
    Download export data from Bandtrass.
    """
    _download_data(output_dir, headless, strategy)

@app.command()
def report(
    start_year: int = typer.Option(2024, "--start-year", "-s", help="Start year for filtering (inclusive)"),
    end_year: int = typer.Option(2025, "--end-year", "-e", help="End year for filtering (inclusive)"),
    output: str = typer.Option("reports/report.xlsx", "--output", "-o", help="Output file path for the report"),
    input_file: str = typer.Option(None, "--input", "-i", help="Input Excel file path. Defaults to latest file in data/."),
    strategy: str = typer.Option(None, "--strategy", help="Name of the strategy to use (appends to filename)")
):
    """
    Generate a full report containing both Monthly and Quarterly data in separate sheets.
    Default filter range is 2024 to 2025.
    """
    if strategy:
        # If user didn't change default output or just want to append
        # Logic: If output is default, append strictly. If user provided output, append there too?
        # User said: "append strategy name ... to dashboard OR report name"
        # Simplest: Insert before extension.
        base, ext = os.path.splitext(output)
        if not base.endswith(f"_{strategy}"):
             output = f"{base}_{strategy}{ext}"
             
    _generate_report(input_file, start_year, end_year, output)

@app.command()
def full(
    start_year: int = typer.Option(2024, "--start-year", "-s", help="Start year for filtering (inclusive)"),
    end_year: int = typer.Option(2025, "--end-year", "-e", help="End year for filtering (inclusive)"),
    output: str = typer.Option("reports/report.xlsx", "--output", "-o", help="Output file path for the report"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode for download"),
    strategy: str = typer.Option(None, "--strategy", help="Name of the strategy to use")
):
    """
    Execute full workflow: Download data -> Generate Report.
    """
    typer.echo("=== [Step 1] Downloading Data ===")
    # Default data directory for full command
    downloaded_file = _download_data("data", headless, strategy)
    
    if strategy:
        base, ext = os.path.splitext(output)
        if not base.endswith(f"_{strategy}"):
             output = f"{base}_{strategy}{ext}"

    # Check if downloaded_file is already a report (in reports directory)
    if "reports" in downloaded_file or "report_" in os.path.basename(downloaded_file):
        typer.echo(f"\n=== [Step 2] Report already generated: {downloaded_file} ===")
        # Use the existing report file
        final_report = downloaded_file
    else:
        typer.echo("\n=== [Step 2] Generating Report ===")
        final_report = _generate_report(downloaded_file, start_year, end_year, output)
    
    typer.echo("\n=== [Step 3] Generating Dashboard ===")
    dashboard_output = "reports/dashboard.xlsx"
    if strategy:
        base, ext = os.path.splitext(dashboard_output)
        if not base.endswith(f"_{strategy}"):
             dashboard_output = f"{base}_{strategy}{ext}"
             
    _generate_dashboard(final_report, start_year, end_year, dashboard_output)

from domain.services.dashboard_generator import DashboardGenerator

def _generate_dashboard(input_file: str, start_year: int, end_year: int, output: str):
    """
    Internal function to generate dashboard.
    """
    if input_file is None:
        try:
            input_file = _get_latest_data_file()
            typer.echo(f"Auto-detected latest input file: {input_file}")
        except Exception as e:
            typer.secho(f"Error: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    typer.echo(f"Generating dashboard from {input_file}...")
    typer.echo(f"Filtering range: {start_year} ~ {end_year}")
    
    try:
        # Check if input is already a report file
        if "reports" in input_file or "report_" in os.path.basename(input_file):
            # Already processed report - read directly
            typer.echo("Reading processed report file...")
            monthly_df_all = pd.read_excel(input_file)
        else:
            # Raw data file - process it
            # 1. Read
            adapter = ExcelReaderAdapter()
            raw_df = adapter.read(input_file)
            
            # 2. Process Monthly
            processor = DataProcessor()
            monthly_df_all = processor.process(raw_df)
        
        # 3. Enrich Data (Calculate Daily Avg, MoM, YoY on FULL data)
        generator = DashboardGenerator()
        typer.echo("Enriching data with Business Days and Daily Averages...")
        enriched_all = generator.enrich_data(monthly_df_all)
        
        # 4. Filter
        processor = DataProcessor()
        monthly_df_filtered = processor.filter_by_year(enriched_all, start_year, end_year)
        
        # 5. Generate Dashboard
        typer.echo(f"Generating dashboard with {len(monthly_df_filtered)} records...")
        generator.generate(input_file, monthly_df_filtered, output)
        
        typer.echo(f"Successfully generated dashboard at {output}")
        return output
        
    except Exception as e:
        typer.secho(f"Error generating dashboard: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def dashboard(
    start_year: int = typer.Option(2024, "--start-year", "-s", help="Start year for filtering (inclusive)"),
    end_year: int = typer.Option(2025, "--end-year", "-e", help="End year for filtering (inclusive)"),
    output: str = typer.Option("reports/dashboard.xlsx", "--output", "-o", help="Output file path for the dashboard"),
    input_file: str = typer.Option(None, "--input", "-i", help="Input Excel file path. Defaults to latest file in data/."),
    strategy: str = typer.Option(None, "--strategy", help="Name of the strategy to use (appends to filename)")
):
    """
    Generate a dashboard Excel file with specific layout (Title at A1, Headers at A2).
    """

    if strategy:
        base, ext = os.path.splitext(output)
        if not base.endswith(f"_{strategy}"):
             output = f"{base}_{strategy}{ext}"

    _generate_dashboard(input_file, start_year, end_year, output)

if __name__ == "__main__":
    app()
