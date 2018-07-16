import argparse
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--source', help='video file')
parser.add_argument('--loss_rate', type=int, choices=xrange(0,100), default=1, help='number of lost chunks in percent')
parser.add_argument('--chunk_size', type=int, default=1024, help='size of video chunks')
parser.add_argument('--header_size', type=int, default=10, help='size of video header in chunks')
parser.add_argument('--mode',  choices=['p2psp','chain'], default='p2psp', help='p2psp or chain is possible')
parser.add_argument('--loss_start', type=int, choices=[0, 1, 2], default=1, help='[only for chain mode] 0. just after header, 1. mid-play, 2. near the end')
parser.add_argument('--loss_style', choices=['remove','copy','empty'], default='remove', help='remove: delete de chunk, copy: copy the last chunk available')
parser.add_argument('--output', default='output', help='save the result as...')
args = parser.parse_args()


source=args.source
loss_rate=args.loss_rate
chunk_size=args.chunk_size
header_size=args.header_size
mode=args.mode
loss_start=args.loss_start
loss_style=args.loss_style
output=args.output

lost_chunks=0
current_chunk=0
file_dev=open('/dev/zero','rb')
empty_chunk=file_dev.read(chunk_size) 

file_input=open(source,'rb')

total_chunks=((os.fstat(file_input.fileno()).st_size)-(header_size*chunk_size))/chunk_size
print 'total chunks: ', total_chunks
loss_limit= int(total_chunks*(float(loss_rate)/100))
print 'loss limit: ', loss_limit

if loss_start==0:
	loss_starting=0
elif loss_start==1:
	loss_starting=(total_chunks/2)-(loss_limit/2)
elif loss_start==2:
	loss_starting=total_chunks-loss_limit

file_output=file(output,'wb')

try:
	#discarding the header
	for x in range(1,header_size):
		chunk = file_input.read(chunk_size) 
		file_output.write(chunk)
		#sys.stdout.write('H')

	old_chunk=chunk
	chunk = file_input.read(chunk_size)
	while chunk:
		if mode=='p2psp':
			if (current_chunk%(total_chunks/loss_limit)==0) and (lost_chunks<loss_limit):
				lost_chunks=lost_chunks+1
				if loss_style=="copy":
					file_output.write(old_chunk)
				if loss_style=="empty":
					file_output.write(empty_chunk)
				#sys.stdout.write('#')
			else:
				file_output.write(chunk)
				old_chunk=chunk
				#sys.stdout.write('*')
		elif mode=='chain':
			if (loss_starting<=current_chunk) and (lost_chunks<loss_limit):
				lost_chunks=lost_chunks+1
				if loss_style=="copy":
					file_output.write(old_chunk)
				if loss_style=="empty":
					file_output.write(empty_chunk)
				#sys.stdout.write('#')
			else:
				file_output.write(chunk)
				old_chunk=chunk
				#sys.stdout.write('*')

		chunk = file_input.read(chunk_size)
		current_chunk=current_chunk+1	


finally:
	print 'End of File'
	file_input.close()
	file_output.close()

print 'lost chunks: ',lost_chunks
