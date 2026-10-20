import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Repair RAG MCP")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("index", help="Offline indexing; does not modify business data")
    normalize = commands.add_parser("normalize", help="Convert one observation with OpenAI; no vector index needed")
    normalize.add_argument("text", help="기사의 한국어 소견")
    serve = commands.add_parser("serve")
    serve.add_argument("service", choices=["observation", "pcb", "damage", "rag"])
    serve.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int)
    args = parser.parse_args()
    if args.command == "normalize":
        from .normalize import normalize_observations
        try:
            print(json.dumps(normalize_observations(args.text), ensure_ascii=False, indent=2))
        except (ValueError, RuntimeError) as error:
            parser.exit(1, f"{error}\n")
    elif args.command == "index":
        from .retrieval import DenseStore
        store = DenseStore()
        try:
            print(json.dumps(store.index(), ensure_ascii=False, indent=2))
        finally:
            store.close()
    else:
        from .servers import create_server
        server = create_server(args.service)
        if args.transport == "http":
            port = args.port or {"observation": 8011, "pcb": 8012, "damage": 8013, "rag": 8014}[args.service]
            server.run(transport="http", host=args.host, port=port, path="/mcp")
        else:
            server.run(transport="stdio")


if __name__ == "__main__":
    main()
