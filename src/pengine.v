`ifndef PENGINE_H
`define PENGINE_H

`default_nettype none
module pengine (
    input  wire       rst,
    input  wire       clk,
    input  wire       frame_tick,
    input  wire       cmd_valid,
    input  wire [1:0] cmd_type,
    input  wire [5:0] cmd_data,
    output reg  [9:0] x_ball,
    output reg  [9:0] y_ball
);

localparam CMD_SET_X  = 2'b00;
localparam CMD_SET_Y  = 2'b01;
localparam CMD_SET_VX = 2'b10;
localparam CMD_SET_VY = 2'b11;

localparam MOVE_FRAME_LAST = 3'd5;

localparam signed [10:0] X_MIN = 11'sd7;
localparam signed [10:0] X_MAX = 11'sd632;
localparam signed [10:0] Y_MIN = 11'sd7;
localparam signed [10:0] Y_MAX = 11'sd472;

reg signed [9:0] vx;
reg signed [9:0] vy;
reg        [2:0] frame_count;

wire signed [5:0] signed_cmd_data = cmd_data;
wire              move_tick = frame_tick && (frame_count == MOVE_FRAME_LAST);
wire signed [10:0] next_x = $signed({1'b0, x_ball}) + $signed({vx[9], vx});
wire signed [10:0] next_y = $signed({1'b0, y_ball}) + $signed({vy[9], vy});

always @(posedge clk) begin
    if (rst) begin
        x_ball <= 10'd0;
        y_ball <= 10'd0;
        vx <= 10'sd0;
        vy <= 10'sd0;
        frame_count <= 3'd0;
    end else begin
        if (frame_tick) begin
            if (frame_count == MOVE_FRAME_LAST) begin
                frame_count <= 3'd0;
            end else begin
                frame_count <= frame_count + 3'd1;
            end
        end

        if (cmd_valid) begin
            case (cmd_type)
                CMD_SET_X: begin
                    x_ball <= {1'b0, cmd_data, 3'b000};
                end
                CMD_SET_Y: begin
                    y_ball <= {1'b0, cmd_data, 3'b000};
                end
                CMD_SET_VX: begin
                    if (signed_cmd_data > 6'sd10) begin
                        vx <= 10'sd10;
                    end else if (signed_cmd_data < -6'sd10) begin
                        vx <= -10'sd10;
                    end else begin
                        vx <= {{4{signed_cmd_data[5]}}, signed_cmd_data};
                    end
                end
                CMD_SET_VY: begin
                    if (signed_cmd_data > 6'sd10) begin
                        vy <= 10'sd10;
                    end else if (signed_cmd_data < -6'sd10) begin
                        vy <= -10'sd10;
                    end else begin
                        vy <= {{4{signed_cmd_data[5]}}, signed_cmd_data};
                    end
                end
                default: begin
                end
            endcase
        end else if (move_tick) begin
            if (vx != 10'sd0) begin
                if (next_x < X_MIN) begin
                    x_ball <= X_MIN[9:0];
                    if (vx < 10'sd0) begin
                        vx <= -vx;
                    end
                end else if (next_x > X_MAX) begin
                    x_ball <= X_MAX[9:0];
                    if (vx > 10'sd0) begin
                        vx <= -vx;
                    end
                end else begin
                    x_ball <= next_x[9:0];
                end
            end

            if (vy != 10'sd0) begin
                if (next_y < Y_MIN) begin
                    y_ball <= Y_MIN[9:0];
                    if (vy < 10'sd0) begin
                        vy <= -vy;
                    end
                end else if (next_y > Y_MAX) begin
                    y_ball <= Y_MAX[9:0];
                    if (vy > 10'sd0) begin
                        vy <= -vy;
                    end
                end else begin
                    y_ball <= next_y[9:0];
                end
            end
        end
    end
end

endmodule

`endif
