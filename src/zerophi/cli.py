import click, os, json, sys, asyncio
from .config import RedactionConfig
from .pipelines.redaction import RedactionPipeline
from .processors.documents import DocumentRedactionService, DocumentProcessorFactory
from .performance.optimization import BatchProcessor
from .security import SecureAuditLogger, ComplianceValidator, ZeroTrustValidator, ComplianceStandard, SecureConfiguration
from rich import print
from rich.progress import Progress, TaskID
from rich.console import Console
from rich.table import Table
import time

console = Console()

@click.group()
def app():
    """Advanced PII/PSI/PHI redaction CLI for ZeroPhi"""
    pass

@app.command()
@click.option("--text", type=str, help="Text to redact (use --infile for files)")
@click.option("--infile", type=click.Path(exists=True), help="Path to input text file")
@click.option("--outfile", type=click.Path(), help="Path to output file")
@click.option("--country", default="AU", show_default=True, help="Country code (AU, US, EU, UK, CA)")
@click.option("--company", default=None, help="Company policy overlay")
@click.option("--detectors", default="regex,custom,spacy", help="Comma-separated detector list")
@click.option("--use-openmed", is_flag=True, default=False, help="Enable OpenMed detector")
@click.option("--use-bert", is_flag=True, default=False, help="Enable BERT detector")
@click.option("--use-statistical", is_flag=True, default=False, help="Enable statistical detector")
@click.option("--masking-style", default="hash", 
              type=click.Choice(["hash", "mask", "replace", "brackets", "encrypt", "synthetic", "preserve_format"]),
              help="Redaction strategy")
@click.option("--parallel", is_flag=True, default=True, help="Use parallel processing")
@click.option("--use-cache", is_flag=True, default=True, help="Enable caching")
@click.option("--include-stats", is_flag=True, default=False, help="Include performance statistics")
def redact(text, infile, outfile, country, company, detectors, use_openmed, use_bert, 
          use_statistical, masking_style, parallel, use_cache, include_stats):
    """Redact a text string or file with advanced options"""
    
    # Get input text
    if text:
        data = text
    elif infile:
        with open(infile, "r", encoding="utf-8") as f:
            data = f.read()
    else:
        print("[red]Provide --text or --infile[/red]")
        sys.exit(2)
    
    # Configure pipeline
    detector_list = [d.strip() for d in detectors.split(",")]
    
    cfg = RedactionConfig(
        country=country,
        company=company,
        detectors=detector_list,
        use_openmed=use_openmed,
        use_bert=use_bert,
        use_statistical=use_statistical,
        masking_style=masking_style,
        parallel_detection=parallel,
        cache_detections=use_cache
    )
    
    # Create pipeline and redact
    with console.status("[bold green]Processing text..."):
        start_time = time.time()
        pipe = RedactionPipeline.from_config(cfg)
        result = pipe.redact(data)
        processing_time = time.time() - start_time
    
    # Prepare output
    output_data = {
        "redacted_text": result["text"],
        "entities_found": len(result.get("spans", [])),
        "processing_time": processing_time
    }
    
    if include_stats:
        output_data.update({
            "spans": result.get("spans", []),
            "stats": result.get("stats", {}),
            "performance": pipe.get_performance_summary()
        })
    
    # Output results
    if outfile:
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"[green]Results written to {outfile}[/green]")
    else:
        print(json.dumps(output_data, ensure_ascii=False, indent=2))

@app.command("batch-redact")
@click.option("--indir", type=click.Path(exists=True), required=True, help="Input directory with text files")
@click.option("--outdir", type=click.Path(), required=True, help="Output directory")
@click.option("--pattern", default="*.txt", help="File pattern to match")
@click.option("--country", default="AU", help="Country code")
@click.option("--detectors", default="regex,custom", help="Comma-separated detector list")
@click.option("--masking-style", default="hash", help="Redaction strategy")
@click.option("--max-workers", default=4, help="Maximum worker threads")
@click.option("--batch-size", default=10, help="Batch size for processing")
def batch_redact(indir, outdir, pattern, country, detectors, masking_style, max_workers, batch_size):
    """Batch redact multiple files"""
    import glob
    
    # Find input files
    files = glob.glob(os.path.join(indir, pattern))
    if not files:
        print(f"[red]No files found matching pattern {pattern} in {indir}[/red]")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(outdir, exist_ok=True)
    
    # Configure pipeline
    detector_list = [d.strip() for d in detectors.split(",")]
    cfg = RedactionConfig(
        country=country,
        detectors=detector_list,
        masking_style=masking_style,
        max_workers=max_workers,
        batch_size=batch_size
    )
    
    pipe = RedactionPipeline.from_config(cfg)
    
    # Process files with progress bar
    with Progress() as progress:
        task = progress.add_task("Processing files...", total=len(files))
        
        def progress_callback(current_progress, batch_num, total_batches):
            progress.update(task, completed=batch_num * batch_size)
        
        # Read all file contents
        texts = []
        filenames = []
        for file_path in files:
            with open(file_path, 'r', encoding='utf-8') as f:
                texts.append(f.read())
                filenames.append(os.path.basename(file_path))
        
        # Batch redact
        results = pipe.batch_redact(texts, progress_callback)
        
        # Save results
        for i, (result, filename) in enumerate(zip(results, filenames)):
            if result:
                output_path = os.path.join(outdir, f"redacted_{filename}")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            
            progress.update(task, completed=i + 1)
    
    print(f"[green]Processed {len(files)} files. Results saved to {outdir}[/green]")

@app.command("redact-file")
@click.option("--infile", type=click.Path(exists=True), required=True, help="Input file (PDF, DOCX, TXT, CSV)")
@click.option("--outfile", type=click.Path(), help="Output file path")
@click.option("--country", default="AU", help="Country code")
@click.option("--detectors", default="regex,custom", help="Detectors to use")
@click.option("--masking-style", default="hash", help="Redaction strategy")
@click.option("--preserve-format", is_flag=True, default=True, help="Preserve original formatting")
def redact_file(infile, outfile, country, detectors, masking_style, preserve_format):
    """Redact various file formats while preserving structure"""
    
    # Determine content type
    _, ext = os.path.splitext(infile.lower())
    content_type_map = {
        '.txt': 'text/plain',
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.csv': 'text/csv'
    }
    
    content_type = content_type_map.get(ext)
    if not content_type:
        print(f"[red]Unsupported file type: {ext}[/red]")
        sys.exit(1)
    
    # Configure pipeline
    detector_list = [d.strip() for d in detectors.split(",")]
    cfg = RedactionConfig(
        country=country,
        detectors=detector_list,
        masking_style=masking_style
    )
    
    pipe = RedactionPipeline.from_config(cfg)
    doc_service = DocumentRedactionService(pipe)
    
    # Read file
    with open(infile, 'rb') as f:
        content = f.read()
    
    # Process document
    with console.status("[bold green]Processing document..."):
        result = asyncio.run(doc_service.redact_document(
            content, content_type, preserve_format
        ))
    
    if not result["success"]:
        print(f"[red]Failed to process document: {result.get('error', 'Unknown error')}[/red]")
        sys.exit(1)
    
    # Save result
    if not outfile:
        name, ext = os.path.splitext(infile)
        outfile = f"{name}_redacted{ext}"
    
    with open(outfile, 'wb') as f:
        f.write(result["redacted_content"])
    
    # Display stats
    table = Table(title="Redaction Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Original Size", f"{result['original_size']:,} bytes")
    table.add_row("Redacted Size", f"{result['redacted_size']:,} bytes")
    table.add_row("Entities Found", str(result['entities_found']))
    table.add_row("Output Format", result['output_format'])
    table.add_row("Output File", outfile)
    
    console.print(table)

@app.command("benchmark")
@click.option("--infile", type=click.Path(exists=True), help="File with test cases")
@click.option("--country", default="AU", help="Country to benchmark")
@click.option("--num-samples", default=100, help="Number of test samples")
@click.option("--compare-azure", is_flag=True, help="Compare with Azure PII service")
@click.option("--output-report", type=click.Path(), help="Save benchmark report")
def benchmark(infile, country, num_samples, compare_azure, output_report):
    """Run performance benchmarks"""
    from .evaluators.bench_azure import run_benchmark
    
    # Load test data
    if infile:
        with open(infile, 'r') as f:
            test_texts = [line.strip() for line in f.readlines()[:num_samples]]
    else:
        # Generate sample test data
        test_texts = [
            "John Smith, DOB 1985-03-15, SSN 123-45-6789, lives at 123 Main St",
            "Contact Alice Johnson at alice@example.com or 555-123-4567",
            "Patient ID: P123456, Medicare: 1234-567-890-A, Phone: (555) 987-6543"
        ] * (num_samples // 3)
    
    # Configure ZeroPhi
    cfg = RedactionConfig(country=country, parallel_detection=True, cache_detections=True)
    pipe = RedactionPipeline.from_config(cfg)
    
    console.print(f"[blue]Running benchmark with {len(test_texts)} samples...[/blue]")
    
    # Benchmark ZeroPhi
    zerophi_results = []
    with Progress() as progress:
        task = progress.add_task("Benchmarking ZeroPhi...", total=len(test_texts))
        
        start_time = time.time()
        for i, text in enumerate(test_texts):
            result = pipe.redact(text)
            zerophi_results.append(result)
            progress.update(task, advance=1)
        zerophi_time = time.time() - start_time
    
    # Calculate ZeroPhi metrics
    zerophi_entities = sum(len(r.get('spans', [])) for r in zerophi_results)
    zerophi_throughput = len(test_texts) / zerophi_time
    
    # Benchmark report
    report = {
        "zerophi": {
            "total_time": zerophi_time,
            "throughput": zerophi_throughput,
            "total_entities": zerophi_entities,
            "avg_entities_per_text": zerophi_entities / len(test_texts)
        }
    }
    
    # Compare with Azure if requested
    if compare_azure:
        console.print("[blue]Comparing with Azure PII service...[/blue]")
        try:
            azure_results = run_benchmark(test_texts[:10])  # Limit for API costs
            report["azure_comparison"] = azure_results
        except Exception as e:
            console.print(f"[red]Azure comparison failed: {e}[/red]")
    
    # Performance summary table
    table = Table(title="Benchmark Results")
    table.add_column("Service", style="cyan")
    table.add_column("Time (s)", style="green")
    table.add_column("Throughput (texts/s)", style="green")
    table.add_column("Entities Found", style="green")
    
    table.add_row(
        "ZeroPhi",
        f"{zerophi_time:.2f}",
        f"{zerophi_throughput:.1f}",
        str(zerophi_entities)
    )
    
    console.print(table)
    
    # Save report
    if output_report:
        with open(output_report, 'w') as f:
            json.dump(report, f, indent=2)
        console.print(f"[green]Benchmark report saved to {output_report}[/green]")

@app.command("download-model")
@click.option("--name", default="openmed-base", show_default=True)
@click.option("--models-dir", default=None)
def download_model(name, models_dir):
    """Download an optional model into the local cache"""
    from .models.manager import ensure_model
    path = ensure_model(name, models_dir)
    print(path)

@app.command("show-policy")
@click.option("--country", default="AU", show_default=True)
@click.option("--company", default=None)
def show_policy(country, company):
    """Show the active policy (country + company overlay)"""
    from .policies.loader import load_policy
    import yaml
    pol = load_policy(country, company)
    print(yaml.safe_dump(pol, sort_keys=True))

@app.command("serve")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--workers", default=1, help="Number of worker processes")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(host, port, workers, reload):
    """Start the ZeroPhi API server"""
    import uvicorn
    from .api.rest import app as api_app
    
    console.print(f"[green]Starting ZeroPhi API server on {host}:{port}[/green]")
    console.print(f"[blue]API docs available at: http://{host}:{port}/docs[/blue]")
    
    uvicorn.run(
        "zerophi.api.rest:app",
        host=host,
        port=port,
        workers=workers,
        reload=reload
    )

@app.command("validate")
@click.option("--config-file", type=click.Path(exists=True), help="Configuration file to validate")
@click.option("--country", default="AU", help="Country policy to validate")
def validate(config_file, country):
    """Validate configuration and policies"""
    
    console.print("[blue]Validating ZeroPhi configuration...[/blue]")
    
    # Validate configuration
    try:
        if config_file:
            import yaml
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            cfg = RedactionConfig(**config_data)
        else:
            cfg = RedactionConfig(country=country)
        
        console.print("[green]VALID: Configuration is valid[/green]")
    except Exception as e:
        console.print(f"[red]✗ Configuration error: {e}[/red]")
        return
    
    # Validate policies
    try:
        from .policies.loader import load_policy
        policy = load_policy(cfg.country, cfg.company)
        console.print(f"[green]LOADED: Policy loaded for {cfg.country}[/green]")
        
        # Check required patterns
        required_patterns = ["PERSON_NAME", "EMAIL", "PHONE"]
        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in policy.get("regex_patterns", {}):
                missing_patterns.append(pattern)
        
        if missing_patterns:
            console.print(f"[yellow]WARNING: Missing recommended patterns: {missing_patterns}[/yellow]")
        else:
            console.print("[green]COMPLETE: All recommended patterns present[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Policy error: {e}[/red]")
        return
    
    # Test pipeline creation
    try:
        pipe = RedactionPipeline.from_config(cfg)
        console.print("[green]SUCCESS: Pipeline created successfully[/green]")
        
        # Test with sample text
        test_text = "Test with John Doe, email john@example.com"
        result = pipe.redact(test_text)
        console.print(f"[green]COMPLETE: Test redaction completed ({len(result.get('spans', []))} entities found)[/green]")
        
    except Exception as e:
        console.print(f"[red]✗ Pipeline error: {e}[/red]")
        return
    
    console.print("[bold green]All validations passed![/bold green]")

@app.command("stats")
@click.option("--pipeline-config", help="Pipeline configuration to analyze")
@click.option("--clear-cache", is_flag=True, help="Clear performance cache")
def stats(pipeline_config, clear_cache):
    """Show performance statistics and recommendations"""
    
    # Create default pipeline if no config specified
    cfg = RedactionConfig()
    pipe = RedactionPipeline.from_config(cfg)
    
    if clear_cache:
        pipe.clear_cache()
        console.print("[green]Cache cleared[/green]")
        return
    
    # Get performance summary
    summary = pipe.get_performance_summary()
    
    if not summary:
        console.print("[yellow]No performance data available. Run some redactions first.[/yellow]")
        return
    
    # Performance table
    table = Table(title="Performance Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in summary.items():
        if key == "recommendations":
            continue
        if isinstance(value, float):
            table.add_row(key.replace("_", " ").title(), f"{value:.4f}")
        else:
            table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(table)
    
    # Recommendations
    if "recommendations" in summary and summary["recommendations"]:
        console.print("\n[bold blue]Performance Recommendations:[/bold blue]")
        for rec in summary["recommendations"]:
            console.print(f"• {rec}")

@app.group()
def security():
    """Security and compliance management commands"""
    pass

@security.command()
@click.option("--config-file", default="./configs/security_compliance.yml", 
              help="Path to security configuration file")
def audit_logs(config_file):
    """View audit logs with filtering options"""
    from datetime import datetime, timedelta
    
    try:
        # Initialize audit logger
        audit_logger = SecureAuditLogger()
        
        # Query recent logs (last 24 hours)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        logs = audit_logger.query_audit_logs(
            start_date=start_date,
            end_date=end_date
        )
        
        if not logs:
            console.print("[yellow]No audit logs found for the last 24 hours[/yellow]")
            return
        
        # Display logs in table
        table = Table(title="Recent Audit Logs")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Event Type", style="green")
        table.add_column("Operation", style="blue")
        table.add_column("User ID", style="magenta")
        table.add_column("Risk Level", style="red")
        
        for log in logs[-20:]:  # Show last 20 entries
            table.add_row(
                log.get("timestamp", "")[:19],  # Truncate timestamp
                log.get("event_type", ""),
                log.get("operation", ""),
                log.get("user_id", "N/A"),
                log.get("risk_level", "")
            )
        
        console.print(table)
        console.print(f"\n[green]Showing {len(logs[-20:])} of {len(logs)} total log entries[/green]")
        
    except Exception as e:
        console.print(f"[red]Error accessing audit logs: {e}[/red]")

@security.command()
@click.option("--user-id", help="User ID for context")
@click.option("--purpose", default="test", help="Processing purpose")
@click.option("--data-classification", default="SENSITIVE", 
              type=click.Choice(["PUBLIC", "INTERNAL", "SENSITIVE", "RESTRICTED"]),
              help="Data classification level")
def compliance_check(user_id, purpose, data_classification):
    """Perform compliance validation check"""
    
    try:
        # Initialize compliance validator
        validator = ComplianceValidator([
            ComplianceStandard.GDPR,
            ComplianceStandard.HIPAA,
            ComplianceStandard.PCI_DSS
        ])
        
        # Sample request data
        request_data = {
            "text_length": 1000,
            "processing_purpose": purpose,
            "entity_types": ["SSN", "CREDIT_CARD", "EMAIL"]
        }
        
        user_context = {
            "user_id": user_id,
            "lawful_basis": "legitimate_interest",
            "consent_obtained": False,
            "authorized_user": True,
            "data_classification": data_classification
        }
        
        # Validate compliance
        result = validator.validate_redaction_request(request_data, user_context)
        
        # Display results
        if result["compliant"]:
            console.print("[green]PASSED: Compliance validation PASSED[/green]")
        else:
            console.print("[red]FAILED: Compliance validation FAILED[/red]")
        
        if result["violations"]:
            console.print("\n[bold red]Violations:[/bold red]")
            for violation in result["violations"]:
                console.print(f"• {violation}")
        
        if result["recommendations"]:
            console.print("\n[bold blue]Recommendations:[/bold blue]")
            for rec in result["recommendations"]:
                console.print(f"• {rec}")
        
        if result["required_actions"]:
            console.print("\n[bold yellow]Required Actions:[/bold yellow]")
            for action in result["required_actions"]:
                console.print(f"• {action}")
                
    except Exception as e:
        console.print(f"[red]Error during compliance check: {e}[/red]")

@security.command()
@click.option("--ip-address", default="192.168.1.100", help="IP address for testing")
@click.option("--user-id", help="User ID for testing")
def zero_trust_test(ip_address, user_id):
    """Test Zero Trust security validation"""
    
    try:
        # Initialize Zero Trust validator
        validator = ZeroTrustValidator()
        
        # Sample request context
        request_context = {
            "user_authenticated": True,
            "mfa_verified": False,
            "certificate_based_auth": False,
            "device_managed": True,
            "device_encrypted": True,
            "antivirus_updated": True,
            "os_patched": True,
            "internal_network": ip_address.startswith("192.168."),
            "vpn_connection": False,
            "geo_location_verified": True,
            "known_ip_address": True,
            "business_hours": True,
            "authorized_application": True,
            "rate_limit_compliant": True,
            "unusual_access_pattern": False,
            "suspicious_volume": False,
            "anomalous_timing": False,
            "data_classification": "SENSITIVE"
        }
        
        # Validate request
        result = validator.validate_request(request_context)
        
        # Display results
        trust_score = result["trust_score"]
        if result["trusted"]:
            console.print(f"[green]PASSED: Zero Trust validation PASSED - Trust Score: {trust_score:.1f}%[/green]")
        else:
            console.print(f"[red]FAILED: Zero Trust validation FAILED - Trust Score: {trust_score:.1f}%[/red]")
        
        # Show detailed scores
        table = Table(title="Zero Trust Validation Details")
        table.add_column("Factor", style="cyan")
        table.add_column("Score", style="green")
        table.add_column("Max Score", style="blue")
        
        for factor, score in result["details"].items():
            table.add_row(factor.replace("_", " ").title(), str(score), "10")
        
        console.print(table)
        
        if result["recommendations"]:
            console.print("\n[bold yellow]Security Recommendations:[/bold yellow]")
            for rec in result["recommendations"]:
                console.print(f"• {rec}")
                
    except Exception as e:
        console.print(f"[red]Error during Zero Trust validation: {e}[/red]")

@security.command()
def config_security():
    """Configure security and compliance settings"""
    
    try:
        # Initialize secure configuration
        config = SecureConfiguration()
        
        console.print("[bold blue]Current Security Configuration:[/bold blue]")
        
        # Security settings
        security_settings = config.get_security_settings()
        table = Table(title="Security Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in security_settings.items():
            if isinstance(value, dict):
                continue  # Skip nested dicts for now
            table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print(table)
        
        # Compliance settings
        compliance_settings = config.get_compliance_settings()
        table2 = Table(title="Compliance Settings")
        table2.add_column("Setting", style="cyan")
        table2.add_column("Value", style="green")
        
        for key, value in compliance_settings.items():
            if isinstance(value, dict) or isinstance(value, list):
                continue  # Skip complex types for display
            table2.add_row(key.replace("_", " ").title(), str(value))
        
        console.print(table2)
        
        # Show enabled features
        console.print("\n[bold green]Security Features Status:[/bold green]")
        features = [
            ("Encryption at Rest", config.is_feature_enabled("security.encryption_at_rest")),
            ("Audit Logging", config.is_feature_enabled("security.audit_logging")),
            ("Zero Trust Mode", config.is_feature_enabled("security.zero_trust_mode")),
            ("Differential Privacy", config.is_feature_enabled("privacy.differential_privacy_enabled")),
            ("Data Minimization", config.is_feature_enabled("privacy.data_minimization"))
        ]
        
        for feature, enabled in features:
            status = "[green]ENABLED[/green]" if enabled else "[red]DISABLED[/red]"
            console.print(f"• {feature}: {status}")
            
    except Exception as e:
        console.print(f"[red]Error accessing security configuration: {e}[/red]")

@security.command()
@click.option("--event-type", help="Filter by event type")
@click.option("--days", default=7, type=int, help="Number of days to analyze")
def security_report(event_type, days):
    """Generate security and compliance report"""
    from datetime import datetime, timedelta
    
    try:
        # Initialize components
        audit_logger = SecureAuditLogger()
        
        # Query logs for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        logs = audit_logger.query_audit_logs(
            start_date=start_date,
            end_date=end_date,
            event_type=event_type
        )
        
        if not logs:
            console.print(f"[yellow]No logs found for the last {days} days[/yellow]")
            return
        
        # Analyze logs
        event_counts = {}
        risk_levels = {}
        user_activity = {}
        
        for log in logs:
            # Event type analysis
            event_type_log = log.get("event_type", "UNKNOWN")
            event_counts[event_type_log] = event_counts.get(event_type_log, 0) + 1
            
            # Risk level analysis
            risk_level = log.get("risk_level", "UNKNOWN")
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
            
            # User activity analysis
            user_id = log.get("user_id", "ANONYMOUS")
            user_activity[user_id] = user_activity.get(user_id, 0) + 1
        
        # Display report
        console.print(f"[bold blue]Security Report - Last {days} Days[/bold blue]")
        console.print(f"[green]Total Events: {len(logs)}[/green]\n")
        
        # Event types table
        table1 = Table(title="Event Types")
        table1.add_column("Event Type", style="cyan")
        table1.add_column("Count", style="green")
        
        for event, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True):
            table1.add_row(event, str(count))
        
        console.print(table1)
        
        # Risk levels table
        table2 = Table(title="Risk Level Distribution")
        table2.add_column("Risk Level", style="cyan")
        table2.add_column("Count", style="green")
        
        for risk, count in sorted(risk_levels.items(), key=lambda x: x[1], reverse=True):
            color = "red" if risk == "HIGH" else "yellow" if risk == "MEDIUM" else "green"
            table2.add_row(f"[{color}]{risk}[/{color}]", str(count))
        
        console.print(table2)
        
        # Top users table
        table3 = Table(title="Top Active Users")
        table3.add_column("User ID", style="cyan")
        table3.add_column("Activity Count", style="green")
        
        top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]
        for user, count in top_users:
            table3.add_row(user, str(count))
        
        console.print(table3)
        
        # Security alerts
        high_risk_events = [log for log in logs if log.get("risk_level") == "HIGH"]
        if high_risk_events:
            console.print(f"\n[bold red]WARNING: {len(high_risk_events)} High Risk Events Detected![/bold red]")
            console.print("Review these events immediately for potential security incidents.")
        
    except Exception as e:
        console.print(f"[red]Error generating security report: {e}[/red]")

if __name__ == "__main__":
    app()
