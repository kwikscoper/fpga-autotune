`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 06/09/2026 08:42:47 PM
// Design Name: 
// Module Name: audio_file_reader
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module audio_file_reader #(
    parameter CLK_FREQ    = 100_000_000,  // 100 MHz system clock
    parameter SAMPLE_RATE = 15625,         // Hz — must match COE conversion
    parameter SAMPLE_COUNT = 244000        // from wav_to_coe.py output
)(
    input  wire        clk,
    input  wire        rst,
    output reg  [11:0] sample_out,   // 12-bit sample, matches ADC format
    output reg         sample_valid, // high for 1 cycle when sample_out is valid
    output reg         done          // high when file playback is complete
);

// How many clock cycles between each sample output
localparam CYCLES_PER_SAMPLE = CLK_FREQ / SAMPLE_RATE;  // = 6400

// Address width: ceil(log2(SAMPLE_COUNT))
localparam ADDR_BITS = 18;

reg [12:0]          cycle_cnt;
reg [ADDR_BITS-1:0] addr;
wire [15:0]         bram_out;
reg                 bram_valid;

// Instantiate your BRAM IP (name matches what Vivado generated)
audio_bram_rom audio_bram_inst (
    .clka  (clk),
    .addra (addr),
    .douta (bram_out)
);

always @(posedge clk) begin
    if (rst) begin
        cycle_cnt    <= 0;
        addr         <= 0;
        sample_valid <= 0;
        done         <= 0;
        bram_valid   <= 0;
    end else begin
        sample_valid <= 0;

        if (!done) begin
            if (cycle_cnt == CYCLES_PER_SAMPLE - 2) begin
                // Issue BRAM read one cycle early (1-cycle latency)
                bram_valid <= 1;
            end

            if (cycle_cnt == CYCLES_PER_SAMPLE - 1) begin
                cycle_cnt    <= 0;
                sample_out   <= bram_out[11:0];  // lower 12 bits
                sample_valid <= 1;
                bram_valid   <= 0;

                if (addr < SAMPLE_COUNT - 1)
                    addr <= addr + 1;
                else
                    done <= 1;  // end of file
            end else begin
                cycle_cnt <= cycle_cnt + 1;
            end
        end
    end
end

endmodule
