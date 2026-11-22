"""Project command line: setup, generation, ingestion, analytics and verification."""
import argparse
import json
from pathlib import Path
from src.db.connection import db_manager
from src.db.executor import sql_executor
from src.utils.config import PROJECT_ROOT


def main():
    parser = argparse.ArgumentParser(description='Walmart-inspired retail intelligence pipeline')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status', help='Read-only warehouse connection and inventory')
    sub.add_parser('setup', help='Non-destructive schema/procedure/view setup')
    gen = sub.add_parser('generate', help='Generate declared synthetic canonical CSVs')
    gen.add_argument(
        '--mode',
        choices=['small','medium','large','historical_15y'],
        default='small',
    )
    gen.add_argument('--seed', type=int, default=42)
    gen.add_argument('--output', type=Path, default=PROJECT_ROOT/'data/synthetic/small_seed42')
    etl = sub.add_parser('etl', help='Archive, validate, stage and load canonical data')
    etl.add_argument('--input', type=Path, default=PROJECT_ROOT/'data/synthetic/small_seed42')
    sub.add_parser('verify', help='Read-only grain, integrity, audit and reconciliation checks')
    sub.add_parser('analytics', help='Train and evaluate models against actual warehouse data')
    public = sub.add_parser('adapt-public', help='Normalize a public dataset at its native grain')
    public.add_argument('--dataset', choices=['walmart-weekly','uci-online-retail'], required=True)
    public.add_argument('--primary', type=Path, required=True)
    public.add_argument('--features', type=Path)
    public.add_argument('--stores', type=Path)
    public.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'setup':
        sql_executor.run_all_setup_scripts()
    elif args.command == 'generate':
        from src.ingestion.generator import RetailDataGenerator
        RetailDataGenerator(args.mode,args.seed).generate_all(str(args.output))
    elif args.command == 'etl':
        from src.etl.pipeline import load
        print(json.dumps(load(args.input), indent=2))
    elif args.command == 'status':
        with db_manager.session_scope() as cur:
            cur.execute('SELECT @@VERSION AS Version')
            print(cur.fetchone()['Version'].split('\n')[0])
            cur.execute('''SELECT s.name AS SchemaName,t.name AS TableName,SUM(p.rows) AS RowsPresent
                FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id
                JOIN sys.partitions p ON p.object_id=t.object_id AND p.index_id IN (0,1)
                GROUP BY s.name,t.name ORDER BY s.name,t.name''')
            print(json.dumps(cur.fetchall(),indent=2))
    elif args.command == 'verify':
        from src.etl.verify import verify
        report = verify()
        print(json.dumps(report,indent=2,default=str))
        if not report['passed']:
            raise SystemExit(1)
    elif args.command == 'analytics':
        from src.analytics.run import run
        print(json.dumps(run(),indent=2,default=str))
    elif args.command == 'adapt-public':
        from src.ingestion.adapters import adapt_uci_online_retail, adapt_walmart_weekly_sales
        if args.dataset == 'walmart-weekly':
            _, manifest = adapt_walmart_weekly_sales(
                args.primary, args.output, args.features, args.stores
            )
        else:
            _, manifest = adapt_uci_online_retail(args.primary, args.output)
        print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
