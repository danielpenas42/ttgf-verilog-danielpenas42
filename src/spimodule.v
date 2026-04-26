`ifndef SPIMODULE_H
`define SPIMODULE_H

`default_nettype none

module spimodule (
    input  wire       clk,
    input  wire       rst,
    input  wire       cs,
    input  wire       mosi,
    output wire       miso,
    input  wire       sclk,
    output wire [7:0] data_out,
    output reg        val,
    input  wire       rdy
);

reg [6:0] shift_reg;
reg [2:0] counter;
reg       s1, s2, prev, cs1, cs2;
reg       clk_rise;
reg [7:0] data_send;

assign miso     = 1'b0;
assign data_out = data_send;

// Synchronize the external SPI pins into the clk domain and generate a
// one-cycle pulse when the synchronized SCLK rises.
always @(posedge clk) begin
    if (rst) begin
        clk_rise <= 1'b0;
        s1       <= 1'b0;
        s2       <= 1'b0;
        prev     <= 1'b0;
        cs1      <= 1'b1;
        cs2      <= 1'b1;
    end
    else begin
        clk_rise <= 1'b0;
        cs1      <= cs;
        cs2      <= cs1;
        s1       <= sclk;
        s2       <= s1;
        prev     <= s2;

        if (s2 & ~prev) begin
            clk_rise <= 1'b1;
        end
    end
end

// Count bits only while a frame is active and the output byte register is not
// already full.
always @(posedge clk) begin
    if (rst || cs2) begin
        counter <= 3'd0;
    end
    else if (clk_rise & ~val) begin
        counter <= counter + 3'd1;
    end
end

// Shift incoming bits into the receive register only while the byte register
// can still accept new data.
always @(posedge clk) begin
    if (rst || cs2) begin
        shift_reg <= 7'd0;
    end
    else if (clk_rise & ~val) begin
        shift_reg <= {shift_reg, mosi};
    end
end

// Latch the completed byte and hold it until the consumer accepts it.
always @(posedge clk) begin
    if (rst) begin
        val <= 1'b0;
        data_send <= 8'd0;
    end
    else begin
        if (~val & ~cs2 & (counter == 3'd7) & clk_rise) begin
            val <= 1'b1;
            data_send <= {shift_reg[6:0], mosi};
        end

        if (val & rdy) begin
            val <= 1'b0;
        end
    end
end

endmodule

`endif