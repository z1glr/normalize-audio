from pathlib import Path
import shutil
import soundfile
import pyloudnorm

# path of the original files
PTH_ORIG_FILES = Path("origs")
# output directory - gets auto-created
PTH_OUTPUT = Path("output")

def main():
    # store information of the audio-files
    dct_audio_files: dict[Path, any] = {}
    # the individual meters for the different sample rates
    dct_meter = {}

    # search for audio-files
    for pth_ff in PTH_ORIG_FILES.rglob("*"):
        # check, if it is a file
        if pth_ff.is_file():
            try:
                # open the file as a soundfile
                data, f_rate = soundfile.read(pth_ff)

                # store the soundfile in the dictionary
                dct_audio_files[pth_ff] = {"audio": {"orig": data}, "rate": f_rate}

            # Error: file is no audio file
            except soundfile.LibsndfileError:
                print(f"{pth_ff} is no audio-file (copying original to output)")

                # copy the file to the output directory
                shutil.copy(pth_ff, pth_create_output_file_path(pth_ff))


    # check for the audio-file with the lowest loudness crest
    f_lowest_loudness_crest = 0

    print ("analyzing files")

    for pth_ff, data in dct_audio_files.items():
        # peak normalize to -1 dbTP to compare the files
        data_1dbTP = pyloudnorm.normalize.peak(data["audio"]["orig"], -1)

        # create pyloudnorm-meters for each sample rate
        if data["rate"] not in dct_meter:
            dct_meter[data["rate"]] = pyloudnorm.Meter(f_rate)

        # analyze the loudness of the original and the peak normalized file
        data["loudness"] = {"orig": dct_meter[data["rate"]].integrated_loudness(data["audio"]["orig"])}

        f_loudness_data_1dbTP = dct_meter[data["rate"]].integrated_loudness(data_1dbTP)

        # if the file has a new, lowest loudness, store this loudness
        if f_loudness_data_1dbTP < f_lowest_loudness_crest:
            f_lowest_loudness_crest = f_loudness_data_1dbTP

            print (f"lowest loudness crest is {f_lowest_loudness_crest:.2f} LUFS ({pth_ff})")

    print ("normalizing files")

    for pth_ff, data in dct_audio_files.items():
        # normalize to the lowest found loudness crest to make all audio-files the same loudness
        data["audio"]["normalized"] = pyloudnorm.normalize.loudness(data["audio"]["orig"], data["loudness"]["orig"], f_lowest_loudness_crest)
        data["loudness"]["normalized"] = dct_meter[data["rate"]].integrated_loudness(data["audio"]["normalized"])

        pth_out_file = pth_create_output_file_path(pth_ff)

        # export the normalized audio
        if not pth_out_file.exists():
            soundfile.write(pth_out_file, data["audio"]["normalized"], data["rate"])

            print (f"{pth_out_file}: {data["loudness"]["normalized"] - data["loudness"]["orig"]:.2f} dB")
        else:
            print (f"{pth_out_file} already exists - skipping")

def pth_create_output_file_path(pth_orig: Path) -> Path:
    """convert an input-file-path to an output-file-path and create its parent directory

    Args:
        pth_orig (Path): path of the input file

    Returns:
        Path: path for the output file
    """
    pth_output = PTH_OUTPUT / pth_orig.relative_to(PTH_ORIG_FILES)

    if not pth_output.parent.exists():
        pth_output.parent.mkdir(parents=True)

    return pth_output

if __name__ == "__main__":
    main()
