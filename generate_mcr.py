#!/usr/bin/env python3
"""Generate .mcr macro files with mouse grid movements."""

import argparse


def generate_mcr(x1: int, y1: int, x2: int, y2: int, gap_x: int, gap_y: int = None,
                 macro_path: str = "D:\\macro\\AutoAG\\detect-distance.mcr",
                 repeat_count: int = 100) -> str:
    """Generate MCR macro content for a grid of mouse movements.

    Args:
        x1, y1: Starting coordinates
        x2, y2: Ending coordinates
        gap_x: Gap between x positions
        gap_y: Gap between y positions (defaults to gap_x if not specified)
        macro_path: Path to the macro to play at each position
        repeat_count: Number of iterations for the REPEAT block
    """
    if gap_y is None:
        gap_y = gap_x

    lines = []
    lines.append(f"REPEAT : {repeat_count} : 0 : 0 : Enter the number of iterations: : 0 : 0")

    # Generate grid points
    y = y1
    while y <= y2:
        x = x1
        while x <= x2:
            lines.append(f"Mouse : {x} : {y} : Move : 0 : 0 : 0")
            lines.append(f"PLAY MACRO : {macro_path}")
            x += gap_x
        y += gap_y

    # Add ending keyboard actions
    lines.append("Keyboard : A : KeyDown")
    lines.append("DELAY : 1000")
    lines.append("Keyboard : A : KeyUp")
    lines.append("ENDREPEAT")
    lines.append("")  # Empty line at end

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate .mcr macro files")
    parser.add_argument("x1", type=int, help="Starting X coordinate")
    parser.add_argument("y1", type=int, help="Starting Y coordinate")
    parser.add_argument("x2", type=int, help="Ending X coordinate")
    parser.add_argument("y2", type=int, help="Ending Y coordinate")
    parser.add_argument("--gap-x", type=int, default=100, help="Gap between X positions (default: 100)")
    parser.add_argument("--gap-y", type=int, help="Gap between Y positions (default: same as gap-x)")
    parser.add_argument("--macro", default="D:\\macro\\AutoAG\\detect-distance.mcr",
                        help="Path to macro to play at each position")
    parser.add_argument("--repeat", type=int, default=100, help="Repeat count (default: 100)")
    parser.add_argument("-o", "--output", default="output.mcr", help="Output file (default: output.mcr)")

    args = parser.parse_args()

    content = generate_mcr(
        args.x1, args.y1, args.x2, args.y2,
        gap_x=args.gap_x,
        gap_y=args.gap_y,
        macro_path=args.macro,
        repeat_count=args.repeat
    )

    with open(args.output, "w") as f:
        f.write(content)

    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
