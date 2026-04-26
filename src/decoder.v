`ifndef DECODER_H
`define DECODER_H

`default_nettype none
module decoder(
    input  wire       rst,
    input  wire       clk,

    input  wire [7:0] in,
    input  wire       val,
    output wire       rdy,

    output reg  [5:0] cmd_data,
    output reg   [1:0] cmd_type,
    output reg        cmd_valid
);

assign rdy = 1'b1;

always @(posedge clk) begin
    cmd_valid <= 1'b0;
    if (rst) begin
        cmd_valid <= 1'b0;
        cmd_data <= 6'd0;
        cmd_type <= 2'b00;
    end
    else if (val) begin
        cmd_valid <= 1'b1;
        cmd_data <= in[5:0];
        cmd_type <= in[7:6];
    end
end

endmodule

`endif