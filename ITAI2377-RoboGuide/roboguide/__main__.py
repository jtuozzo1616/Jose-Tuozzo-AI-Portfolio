import argparse,json
from .core import RoboGuide,to_dict

def main():
    p=argparse.ArgumentParser(description='RoboGuide: cited offline PiDog support')
    p.add_argument('question',nargs='?',default='Why does my PiDog wobble?')
    p.add_argument('--version',choices=['standard','v2'])
    p.add_argument('--json',action='store_true')
    p.add_argument('--baseline',action='store_true')
    args=p.parse_args()
    model=RoboGuide(variant='baseline' if args.baseline else 'hybrid')
    r=model.ask(args.question,version=args.version)
    if args.json:print(json.dumps(to_dict(r),indent=2,ensure_ascii=False))
    else:
        print('Status:',r.status,'| Evidence strength:',r.evidence_strength,'| Latency:',r.latency_ms,'ms')
        print(r.answer)
        for i,h in enumerate(r.hits,1):print(f'  [S{i}] {h.title} — {h.url}')
if __name__=='__main__':main()
