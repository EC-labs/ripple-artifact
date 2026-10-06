import duckdb
import click
import os


@click.option('--dbs', is_flag=False, metavar='<database-list>', type=click.STRING, help='Comma-seperated list of duckdb databases')
@click.command()
def main(dbs):
    # split columns by ',' and remove whitespace
    if dbs is None:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        return

    dbs = [click.Path(exists=True).convert(db.strip(), None, None) for db in dbs.split(',')]
    print(dbs)
    for db in dbs:
        conn = duckdb.connect(db)
        machine_id = conn.execute("SELECT DISTINCT local_machine_id FROM tcp_discovery").fetchall()[0][0]
        print(machine_id)
        tables = conn.execute("SHOW TABLES").fetchall()
        for (table, ) in tables:
            if table in ("linux_consts", "tcp_discovery", "taskstats_view"):
                continue
            conn.execute(f"""
                ALTER TABLE {table} 
                ADD COLUMN machine_id UINTEGER;

                UPDATE {table} 
                SET machine_id = {machine_id} 
                WHERE true;
            """, [])

main()
