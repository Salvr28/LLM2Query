import argparse
import json
from query_executor import execute_mongodb_query

def main():
    parser = argparse.ArgumentParser(description="Esegui una query MongoDB da terminale.")
    parser.add_argument('--conn', required=True, help='MongoDB connection string, es: mongodb://localhost:27017')
    parser.add_argument('--db', required=True, help='Nome del database MongoDB')
    parser.add_argument('--query', required=True, help='Query Python-style su MongoDB, es: db["ANAGRAFICA"].find({"nome": "Mario"})')

    args = parser.parse_args()

    try:
        result = execute_mongodb_query(args.query, args.conn, args.db)

        if result["success"]:
            print("✅ Risultato della query:")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False))
            print(f"🔍 Tipo: {result['query_type']}")
            print(f"📦 Documenti restituiti: {result['affected_count']}")
        else:
            print("❌ Errore nella query:")
            print(result["error"])
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione: {str(e)}")

if __name__ == '__main__':
    main()
