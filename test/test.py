# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import os
import cocotb
from cocotb.clock import Clock
from cocotb.handle import Force, Release
from cocotb.triggers import ClockCycles


CMD_SET_X = 0b00
CMD_SET_Y = 0b01
CMD_SET_VX = 0b10
CMD_SET_VY = 0b11

IS_GATE_LEVEL = os.environ.get("GATES") == "yes"

CS_BIT = 0
MOSI_BIT = 1
SCLK_BIT = 3


def pack_command(cmd_type, cmd_data):
    """Encode the byte format used by decoder.v: [7:6]=type, [5:0]=data."""
    return ((cmd_type & 0b11) << 6) | (cmd_data & 0b111111)


def encode_signed6(value):
    return value & 0b111111


def make_uio(cs=1, mosi=0, sclk=0):
    """Build the uio_in value for the SPI pins used by the top module."""
    return (cs << CS_BIT) | (mosi << MOSI_BIT) | (sclk << SCLK_BIT)


def assert_value(signal, expected, name):
    actual = int(signal.value)
    assert actual == expected, f"{name}: expected {expected}, got {actual}"


async def reset_dut(dut):
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = make_uio(cs=1, mosi=0, sclk=0)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)


async def spi_send_byte(dut, value):
    """Send one SPI byte MSB first on uio_in[1], with active-low CS on uio_in[0]."""
    dut.uio_in.value = make_uio(cs=0, mosi=0, sclk=0)
    await ClockCycles(dut.clk, 6)

    for bit_index in range(7, -1, -1):
        bit = (value >> bit_index) & 1
        dut.uio_in.value = make_uio(cs=0, mosi=bit, sclk=0)
        await ClockCycles(dut.clk, 6)
        dut.uio_in.value = make_uio(cs=0, mosi=bit, sclk=1)
        await ClockCycles(dut.clk, 6)

    dut.uio_in.value = make_uio(cs=1, mosi=0, sclk=0)
    await ClockCycles(dut.clk, 16)


async def force_frame_tick_low(dut):
    dut.user_project.physics_module.frame_tick.value = Force(0)
    await ClockCycles(dut.clk, 1)


async def pulse_frame_ticks(dut, count):
    for _ in range(count):
        dut.user_project.physics_module.frame_tick.value = Force(1)
        await ClockCycles(dut.clk, 1)
        dut.user_project.physics_module.frame_tick.value = Force(0)
        await ClockCycles(dut.clk, 1)


async def pulse_physics_ticks(dut, count):
    await pulse_frame_ticks(dut, count * 6)


def release_frame_tick(dut):
    dut.user_project.physics_module.frame_tick.value = Release()


@cocotb.test(skip=IS_GATE_LEVEL)
async def test_spi_commands_move_ball(dut):
    dut._log.info("Start")

    # This is the Tiny Tapeout project clock. The exact period is not important
    # for this digital test, but the SPI helper waits several clk cycles so the
    # two-flop synchronizers in spimodule.v can see each SCLK edge.
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    dut._log.info("Reset")
    await reset_dut(dut)

    assert dut.uio_out.value == 0
    assert dut.uio_oe.value == 0
    assert dut.user_project.x_ball.value == 0
    assert dut.user_project.y_ball.value == 0

    dut._log.info("Set X position over SPI")
    await spi_send_byte(dut, pack_command(CMD_SET_X, 12))
    assert_value(dut.user_project.x_ball, 12 << 3, "x_ball after SET_X")
    assert_value(dut.user_project.y_ball, 0, "y_ball after SET_X")

    dut._log.info("Set Y position over SPI")
    await spi_send_byte(dut, pack_command(CMD_SET_Y, 21))
    assert_value(dut.user_project.x_ball, 12 << 3, "x_ball after SET_Y")
    assert_value(dut.user_project.y_ball, 21 << 3, "y_ball after SET_Y")

    dut._log.info("Velocity commands should not move the ball immediately")
    await spi_send_byte(dut, pack_command(CMD_SET_VX, encode_signed6(3)))
    await spi_send_byte(dut, pack_command(CMD_SET_VY, encode_signed6(-2)))
    assert_value(dut.user_project.x_ball, 12 << 3, "x_ball after velocity commands")
    assert_value(dut.user_project.y_ball, 21 << 3, "y_ball after velocity commands")

@cocotb.test(skip=IS_GATE_LEVEL)
async def test_reset_clears_ball(dut):
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    await spi_send_byte(dut, pack_command(CMD_SET_X, 12))
    await spi_send_byte(dut, pack_command(CMD_SET_Y, 21))

    assert_value(dut.user_project.x_ball, 12 << 3, "x_ball before reset")
    assert_value(dut.user_project.y_ball, 21 << 3, "y_ball before reset")

    await reset_dut(dut)

    assert_value(dut.user_project.x_ball, 0, "x_ball after reset")
    assert_value(dut.user_project.y_ball, 0, "y_ball after reset")

@cocotb.test(skip=IS_GATE_LEVEL)
async def test_spi_set_x_and_y(dut):
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    await spi_send_byte(dut, pack_command(CMD_SET_X, 12))
    assert_value(dut.user_project.x_ball, 12 << 3, "x_ball after SET_X")
    assert_value(dut.user_project.y_ball, 0, "y_ball after SET_X")

    await spi_send_byte(dut, pack_command(CMD_SET_Y, 21))
    assert_value(dut.user_project.x_ball, 12 << 3, "x_ball after SET_Y")
    assert_value(dut.user_project.y_ball, 21 << 3, "y_ball after SET_Y")


@cocotb.test(skip=IS_GATE_LEVEL)
async def test_spi_max_values(dut):
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    await spi_send_byte(dut, pack_command(CMD_SET_X, 63))
    await spi_send_byte(dut, pack_command(CMD_SET_Y, 63))

    assert_value(dut.user_project.x_ball, 63 << 3, "x_ball max value")
    assert_value(dut.user_project.y_ball, 63 << 3, "y_ball max value")


@cocotb.test(skip=IS_GATE_LEVEL)
async def test_spi_velocity_moves_ball(dut):
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)
    await force_frame_tick_low(dut)

    await spi_send_byte(dut, pack_command(CMD_SET_X, 20))
    await spi_send_byte(dut, pack_command(CMD_SET_Y, 20))
    await spi_send_byte(dut, pack_command(CMD_SET_VX, encode_signed6(3)))
    await spi_send_byte(dut, pack_command(CMD_SET_VY, encode_signed6(-2)))

    await pulse_physics_ticks(dut, 1)
    assert_value(dut.user_project.x_ball, (20 << 3) + 3, "x_ball after one physics tick")
    assert_value(dut.user_project.y_ball, (20 << 3) - 2, "y_ball after one physics tick")

    await pulse_physics_ticks(dut, 4)
    assert_value(dut.user_project.x_ball, (20 << 3) + 15, "x_ball after five physics ticks")
    assert_value(dut.user_project.y_ball, (20 << 3) - 10, "y_ball after five physics ticks")

    release_frame_tick(dut)


@cocotb.test(skip=IS_GATE_LEVEL)
async def test_spi_velocity_clamps_to_ten(dut):
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)
    await force_frame_tick_low(dut)

    await spi_send_byte(dut, pack_command(CMD_SET_X, 20))
    await spi_send_byte(dut, pack_command(CMD_SET_Y, 20))
    await spi_send_byte(dut, pack_command(CMD_SET_VX, encode_signed6(31)))
    await spi_send_byte(dut, pack_command(CMD_SET_VY, encode_signed6(-32)))

    await pulse_physics_ticks(dut, 1)
    assert_value(dut.user_project.x_ball, (20 << 3) + 10, "x_ball after clamped +vx")
    assert_value(dut.user_project.y_ball, (20 << 3) - 10, "y_ball after clamped -vy")

    release_frame_tick(dut)


@cocotb.test(skip=IS_GATE_LEVEL)
async def test_ball_rebounds_from_left_and_top_edges(dut):
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)
    await force_frame_tick_low(dut)

    await spi_send_byte(dut, pack_command(CMD_SET_X, 1))
    await spi_send_byte(dut, pack_command(CMD_SET_Y, 1))
    await spi_send_byte(dut, pack_command(CMD_SET_VX, encode_signed6(-10)))
    await spi_send_byte(dut, pack_command(CMD_SET_VY, encode_signed6(-10)))

    await pulse_physics_ticks(dut, 1)
    assert_value(dut.user_project.x_ball, 7, "x_ball clamped at left edge")
    assert_value(dut.user_project.y_ball, 7, "y_ball clamped at top edge")

    await pulse_physics_ticks(dut, 1)
    assert_value(dut.user_project.x_ball, 17, "x_ball rebounded from left edge")
    assert_value(dut.user_project.y_ball, 17, "y_ball rebounded from top edge")

    release_frame_tick(dut)


@cocotb.test(skip=IS_GATE_LEVEL)
async def test_ball_rebounds_from_right_and_bottom_edges(dut):
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)
    await force_frame_tick_low(dut)

    await spi_send_byte(dut, pack_command(CMD_SET_X, 63))
    await spi_send_byte(dut, pack_command(CMD_SET_Y, 58))
    await spi_send_byte(dut, pack_command(CMD_SET_VX, encode_signed6(10)))
    await spi_send_byte(dut, pack_command(CMD_SET_VY, encode_signed6(10)))

    await pulse_physics_ticks(dut, 1)
    assert_value(dut.user_project.y_ball, 472, "y_ball clamped at bottom edge")

    await pulse_physics_ticks(dut, 1)
    assert_value(dut.user_project.y_ball, 462, "y_ball rebounded from bottom edge")

    await pulse_physics_ticks(dut, 11)
    assert_value(dut.user_project.x_ball, 632, "x_ball clamped at right edge")

    await pulse_physics_ticks(dut, 1)
    assert_value(dut.user_project.x_ball, 622, "x_ball rebounded from right edge")

    release_frame_tick(dut)


@cocotb.test(skip=not IS_GATE_LEVEL)
async def test_gate_level_public_pins_smoke(dut):
    clock = Clock(dut.clk, 100, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_dut(dut)

    assert_value(dut.uio_oe, 0, "uio_oe after reset")
    assert_value(dut.uio_out, 0, "uio_out after reset")

    await spi_send_byte(dut, pack_command(CMD_SET_X, 12))
    await spi_send_byte(dut, pack_command(CMD_SET_Y, 21))
    await ClockCycles(dut.clk, 20)

    int(dut.uo_out.value)
