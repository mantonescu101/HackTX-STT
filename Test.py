import time
import pdb
import os
import argparse
from rev_ai.speechrec import RevSpeechAPI



def await_transcript(client, id_):
    while client.view_job(id_)['status'] == 'in_progress':
        print('waiting...')
        time.sleep(5)
    return client.get_transcript(id_)


def main():
	
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', '--input', help='file that will be transcribed using rev_ai')

	args = parser.parse_args()

	input_file = args.input	
	
	dir_path = os.path.dirname(os.path.realpath(__file__)) 
	filename = os.path.join(dir_path, input_file)

	client = RevSpeechAPI('01ao_KcVCQtnbg8FgkQFtKSJyiBLHXTWudFxGRlREPBoDiAuwAkX3CtaJIkvPp6tRFJX2MB99Z_chrq2bL5tKBzse6uYw')

	print(client.get_account())
	result = client.submit_job_local_file(filename)

	transcript = await_transcript(client, result['id'])
	for word in transcript['monologues'][0]['elements']:
		print(word['value'])
	
if __name__ == '__main__':
	main()
