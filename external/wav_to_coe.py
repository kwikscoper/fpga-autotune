import numpy as np
from scipy.io import wavfile
from scipy.signal import resample
import sys

def wav_to_coe(input_file, output_file, target_rate=15625, bit_depth=12):
    """
    Converts a WAV file to a Xilinx BRAM .COE initialization file.
    Output samples are 12-bit unsigned (0–4095), matching the ADC format.
    """
    rate, data = wavfile.read(input_file)
    print(f"Input: {rate} Hz, shape={data.shape}, dtype={data.dtype}")

    # Convert stereo to mono
    if len(data.shape) > 1:
        data = data.mean(axis=1)

    # Normalize to float -1.0 to 1.0
    if data.dtype == np.int16:
        data = data.astype(np.float64) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float64) / 2147483648.0
    elif data.dtype == np.uint8:
        data = (data.astype(np.float64) - 128.0) / 128.0

    # Resample to target rate
    num_samples = int(len(data) * target_rate / rate)
    # Cap at ~19 sec worth of BRAM space (leave headroom)
    max_samples = 290000  # ~18.5 seconds at 15625 Hz
    if num_samples > max_samples:
        print(f"WARNING: Trimming to {max_samples} samples ({max_samples/target_rate:.1f}s)")
        num_samples = max_samples
    resampled = resample(data[:int(num_samples * rate / target_rate)], num_samples)

    # Convert to 12-bit unsigned (0–4095)
    # DC bias to center: -1.0 → 0, 0.0 → 2048, +1.0 → 4095
    scaled = ((resampled + 1.0) / 2.0 * (2**bit_depth - 1)).astype(np.uint16)
    scaled = np.clip(scaled, 0, 2**bit_depth - 1)

    # Write COE file
    with open(output_file, 'w') as f:
        f.write('memory_initialization_radix=16;\n')
        f.write('memory_initialization_vector=\n')
        for i, sample in enumerate(scaled):
            suffix = ',' if i < len(scaled) - 1 else ';'
            f.write(f'{sample:03X}{suffix}\n')

    print(f"Output: {output_file}")
    print(f"Samples: {len(scaled)} ({len(scaled)/target_rate:.2f} seconds)")
    print(f"Address bits needed: {int(np.ceil(np.log2(len(scaled))))} bits")
    return len(scaled)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python wav_to_coe.py input.wav output.coe")
        sys.exit(1)
    count = wav_to_coe(sys.argv[1], sys.argv[2])
    print(f"\nIn your Verilog, set SAMPLE_COUNT = {count}")


    '''python3 ./external/wav_to_coe.py ./external/test_files/test_notes_A3_E4_A4_C5.wav audio_mem.coe'''