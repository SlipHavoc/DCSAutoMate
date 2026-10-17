"""Generate a comma-separated list of control names accessible to a specific crew member.

Usage: python tools/genSeatControls.py --module <module> --crew <n> --output <file>

crewAccess is None = accessible to all crew.
crewAccess includes n = accessible to crew member n.
"""
import argparse
import json
import os

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--module', required=True)
	parser.add_argument('--crew', required=True, type=int, help='Crew member index (0=pilot, 1=copilot, 2=crew chief, 3-5=gunners)')
	parser.add_argument('--output', required=True)
	args = parser.parse_args()

	mappingPath = os.path.join('config', 'controlMappings', f'{args.module}.json')
	with open(mappingPath, encoding='utf-8') as f:
		mapping = json.load(f)

	names = []
	for ctrlKey, ctrl in mapping['controls'].items():
		crewAccess = ctrl.get('crewAccess')
		if crewAccess is None or args.crew in crewAccess:
			names.append(ctrlKey)

	names.sort()
	with open(args.output, 'w', encoding='utf-8') as f:
		f.write(','.join(names))

	print(f'Crew {args.crew} controls: {len(names)} → {args.output}')

if __name__ == '__main__':
	main()
