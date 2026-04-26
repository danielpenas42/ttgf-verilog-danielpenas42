/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier:
 */


 /*
  * Project description:
  * 
  * -
*/
`default_nettype none
module tt_um_danielpenas42 (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // VGA-facing signals.
  wire       hsync;
  wire       vsync;
  wire [1:0] R;
  wire [1:0] G;
  wire [1:0] B;
  wire       video_active;
  wire [9:0] pix_x;
  wire [9:0] pix_y;

  // TinyVGA PMOD mapping.
  assign uo_out  = {hsync, B[0], G[0], R[0], vsync, B[1], G[1], R[1]};
  assign uio_out = 0;
  assign uio_oe  = 8'b00000000;


  wire cs   = uio_in[0];
  wire mosi = uio_in[1];
  wire sclk = uio_in[3];
  wire rst  = ~rst_n; // High reset

  wire       spi2m_val;
  wire       spi2m_rdy;
  wire [7:0] spi2m_data;
  wire [5:0] cmd_data;
  wire [1:0] cmd_type;
  wire       cmd_valid;
  wire [9:0] x_ball;
  wire [9:0] y_ball;
  wire       frame_tick;

  wire spi_miso_unused;

  wire _unused = &{ena, ui_in, uio_in[2], uio_in[7:4], spi_miso_unused};

  assign frame_tick = (pix_x == 10'd0) && (pix_y == 10'd0);


  spimodule spi (
    .clk     (clk),
    .rst     (rst),
    .cs      (cs),
    .mosi    (mosi),
    .miso    (spi_miso_unused),
    .sclk    (sclk),
    .data_out(spi2m_data),
    .val     (spi2m_val),
    .rdy     (spi2m_rdy)
  );

  hvsync_generator hvsync_gen (
    .clk       (clk),
    .reset     (rst),
    .hsync     (hsync),
    .vsync     (vsync),
    .display_on(video_active),
    .hpos      (pix_x),
    .vpos      (pix_y)
  );

  decoder send_message( 
    .rst(rst),
    .clk(clk),
    .in(spi2m_data),
    .val(spi2m_val),
    .rdy(spi2m_rdy),
    .cmd_valid(cmd_valid),
    .cmd_type(cmd_type),
    .cmd_data(cmd_data)
  );

  pengine physics_module(
    .rst(rst),
    .clk(clk),
    .frame_tick(frame_tick),
    .cmd_valid(cmd_valid),
    .cmd_type(cmd_type),
    .cmd_data(cmd_data),
    .x_ball(x_ball),
    .y_ball(y_ball)
  );

  vga_display ball_renderer(
    .display_on(video_active),
    .x_ball(x_ball),
    .y_ball(y_ball),
    .hpos(pix_x),
    .vpos(pix_y),
    .R(R),
    .G(G),
    .B(B)
  );


endmodule
