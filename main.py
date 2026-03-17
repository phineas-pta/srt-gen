#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import srt
from datetime import timedelta
from tqdm import tqdm
from pydub import AudioSegment
from tts_wrapper import eSpeakClient

TTS = eSpeakClient()
SAMPLE_RATE = TTS.audio_rate
CHANNELS = TTS.channels
SAMPLE_WIDTH = TTS.sample_width


def srt_gen(subtitles: list[srt.Subtitle]) -> AudioSegment:
	final_audio = AudioSegment.empty()
	previous_end_time = timedelta()

	for entry in tqdm(subtitles, desc="Processing subtitles"):
		if (silence := entry.start - previous_end_time) > timedelta():
			final_audio += AudioSegment.silent(
				duration=1000 * silence.total_seconds() / SAMPLE_RATE,  # weird math otherwise silence is too long
				frame_rate=SAMPLE_RATE
			)
		if (text := entry.content.strip()) != "":
			final_audio += AudioSegment(
				data=TTS.synth_to_bytes(text),
				sample_width=SAMPLE_WIDTH,
				frame_rate=SAMPLE_RATE,
				channels=CHANNELS
			)
			previous_end_time = entry.end  # still inside if block to avoid updating previous_end_time if text is empty

	TTS.cleanup()
	return final_audio


if __name__ == "__main__":

	import argparse
	parser = argparse.ArgumentParser(prog="srt-gen", description="Convert SRT subtitles to a WAV audio file using TTS.", allow_abbrev=False)
	parser.add_argument("-i", "--input", help="Path to the input SRT file.", required=True)
	parser.add_argument("-o", "--output", help="Path to the output WAV file.")
	args = parser.parse_args()

	if not args.input.lower().endswith(".srt") or (args.output is not None and not args.output.lower().endswith(".wav")):
		raise ValueError("Input file must be an SRT file and output file must be a WAV file (if provided).")

	with open(args.input, "r", encoding="utf-8") as f:
		subtitles = list(srt.parse(f.read()))
	res = srt_gen(subtitles)
	if len(res) > 0:
		if args.output is not None:
			output_path = args.output
		else:
			import os.path
			output_path = os.path.splitext(args.input)[0] + ".wav"
			print("No output path provided: output will be saved to same folder as input")
		res.export(output_path, format="wav")
