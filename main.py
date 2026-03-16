#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import srt
from io import BytesIO
from datetime import timedelta
from tqdm import tqdm
from pydub import AudioSegment
from tts_wrapper import SAPIClient

TTS = SAPIClient()
SAMPLE_RATE = TTS.audio_rate


def srt_gen(subtitles: list[srt.Subtitle]) -> AudioSegment:
	final_audio = AudioSegment.empty()
	previous_end_time = timedelta()

	for entry in tqdm(subtitles, desc="Processing subtitles"):
		if (silence := entry.start - previous_end_time) > timedelta():
			final_audio += AudioSegment.silent(duration=1000*silence.total_seconds(), frame_rate=SAMPLE_RATE)
		if (text := entry.content.strip()) != "":
			final_audio += AudioSegment.from_wav(BytesIO(TTS.synth_to_bytes(text)))
			previous_end_time = entry.end  # still inside if block to avoid updating previous_end_time if text is empty

	return final_audio


if __name__ == "__main__":

	import argparse
	parser = argparse.ArgumentParser(prog="srt-gen", description="Convert SRT subtitles to a WAV audio file using TTS.", allow_abbrev=False)
	parser.add_argument("-i", "--input", help="Path to the input SRT file.", required=True)
	parser.add_argument("-o", "--output", help="Path to the output WAV file.")
	args = parser.parse_args()

	with open(args.input, "r", encoding="utf-8") as f:
		subtitles = list(srt.parse(f.read()))
	res = srt_gen(subtitles)
	if len(res) > 0:
		if args.output is None:
			import os.path
			output_path = os.path.splitext(args.input)[0] + ".wav"
			print("No output path provided: output will be saved to same folder as input")
		else:
			output_path = args.output
		res.export(args.output, format="wav")
