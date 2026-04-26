`ifndef VGA_DISPLAY_H
`define VGA_DISPLAY_H

`default_nettype none

module vga_display (
    input  wire       display_on,
    input  wire [9:0] x_ball,
    input  wire [9:0] y_ball,
    input  wire [9:0] hpos,
    input  wire [9:0] vpos,
    output wire [1:0] R,
    output wire [1:0] G,
    output wire [1:0] B
);

localparam RADIUS = 10'd7;

wire [9:0] dx;
wire [9:0] dy;
reg  [9:0] x_limit;
reg        ball_on;

assign dx = (hpos >= x_ball) ? (hpos - x_ball) : (x_ball - hpos);
assign dy = (vpos >= y_ball) ? (vpos - y_ball) : (y_ball - vpos);

always @(*) begin
    x_limit = 10'd0;

    case (dy[4:0])
        5'd0:  x_limit = 10'd7;
        5'd1:  x_limit = 10'd6;
        5'd2:  x_limit = 10'd6;
        5'd3:  x_limit = 10'd6;
        5'd4:  x_limit = 10'd5;
        5'd5:  x_limit = 10'd5;
        5'd6:  x_limit = 10'd3;
        5'd7:  x_limit = 10'd2;
        default: x_limit = 10'd0;
    endcase
end

always @(*) begin
    ball_on = 1'b0;

    if (display_on && (dx <= RADIUS) && (dy <= RADIUS) && (dx <= x_limit)) begin
        ball_on = 1'b1;
    end
end

assign R = ball_on ? 2'b11 : 2'b00;
assign G = ball_on ? 2'b11 : 2'b00;
assign B = ball_on ? 2'b11 : 2'b00;

endmodule

`endif