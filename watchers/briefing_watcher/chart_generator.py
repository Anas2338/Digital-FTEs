"""
ASCII Chart Generator

Generates ASCII-based charts for financial trends and metrics
in the CEO briefing.
"""

from typing import List, Dict, Any, Tuple
import logging

from watchers.briefing_watcher.config import BriefingConfig

logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Generates ASCII charts for briefing visualizations.
    """

    def __init__(self):
        """Initialize chart generator with configuration."""
        self.width = BriefingConfig.CHART_WIDTH
        self.height = BriefingConfig.CHART_HEIGHT
        self.symbols = BriefingConfig.CHART_SYMBOLS

    def generate_bar_chart(
        self,
        data: Dict[str, float],
        title: str = "",
        show_values: bool = True
    ) -> str:
        """
        Generate horizontal bar chart.

        Args:
            data: Dictionary of label -> value
            title: Chart title
            show_values: Whether to show numeric values

        Returns:
            ASCII bar chart as string
        """
        if not data:
            return f"{title}\n(No data available)"

        # Find max value for scaling
        max_value = max(data.values()) if data.values() else 1
        if max_value == 0:
            max_value = 1

        # Calculate bar width (leave space for labels and values)
        label_width = max(len(str(k)) for k in data.keys())
        value_width = 10 if show_values else 0
        bar_width = self.width - label_width - value_width - 5

        chart = []
        if title:
            chart.append(title)
            chart.append("=" * len(title))
            chart.append("")

        for label, value in data.items():
            # Calculate bar length
            bar_length = int((value / max_value) * bar_width)
            bar = self.symbols["bar"] * bar_length

            # Format line
            if show_values:
                line = f"{label:<{label_width}} {bar} ${value:,.2f}"
            else:
                line = f"{label:<{label_width}} {bar}"

            chart.append(line)

        return "\n".join(chart)

    def generate_trend_line(
        self,
        values: List[float],
        labels: List[str] = None,
        title: str = ""
    ) -> str:
        """
        Generate simple trend line chart.

        Args:
            values: List of numeric values
            labels: Optional labels for each value
            title: Chart title

        Returns:
            ASCII trend line as string
        """
        if not values:
            return f"{title}\n(No data available)"

        if labels and len(labels) != len(values):
            labels = None

        # Normalize values to chart height
        min_val = min(values)
        max_val = max(values)
        value_range = max_val - min_val if max_val != min_val else 1

        chart = []
        if title:
            chart.append(title)
            chart.append("=" * len(title))
            chart.append("")

        # Create chart grid
        for row in range(self.height, -1, -1):
            line = []
            threshold = min_val + (value_range * row / self.height)

            for i, value in enumerate(values):
                if value >= threshold:
                    line.append("█")
                else:
                    line.append(" ")

            chart.append("".join(line))

        # Add labels if provided
        if labels:
            label_line = ""
            for label in labels:
                label_line += label[0] if label else " "
            chart.append(label_line)

        return "\n".join(chart)

    def generate_trend_indicator(
        self,
        current: float,
        previous: float
    ) -> Tuple[str, str, float]:
        """
        Generate trend indicator (up/down/flat arrow).

        Args:
            current: Current period value
            previous: Previous period value

        Returns:
            Tuple of (symbol, direction, change_percent)
        """
        if previous == 0:
            if current > 0:
                return self.symbols["trend_up"], "up", 100.0
            else:
                return self.symbols["trend_flat"], "flat", 0.0

        change_percent = ((current - previous) / previous) * 100

        if change_percent > 5:
            return self.symbols["trend_up"], "up", change_percent
        elif change_percent < -5:
            return self.symbols["trend_down"], "down", change_percent
        else:
            return self.symbols["trend_flat"], "flat", change_percent

    def generate_comparison_chart(
        self,
        current_data: Dict[str, float],
        previous_data: Dict[str, float],
        title: str = ""
    ) -> str:
        """
        Generate comparison chart showing current vs previous period.

        Args:
            current_data: Current period data
            previous_data: Previous period data
            title: Chart title

        Returns:
            ASCII comparison chart as string
        """
        chart = []
        if title:
            chart.append(title)
            chart.append("=" * len(title))
            chart.append("")

        # Combine all keys
        all_keys = set(current_data.keys()) | set(previous_data.keys())

        for key in sorted(all_keys):
            current = current_data.get(key, 0)
            previous = previous_data.get(key, 0)

            symbol, direction, change = self.generate_trend_indicator(current, previous)

            line = f"{key:<20} ${current:>10,.2f} {symbol} {change:>6.1f}%"
            chart.append(line)

        return "\n".join(chart)

    def generate_sparkline(self, values: List[float]) -> str:
        """
        Generate compact sparkline (single line trend).

        Args:
            values: List of numeric values

        Returns:
            Single-line sparkline string
        """
        if not values:
            return ""

        # Use Unicode block characters for sparkline
        blocks = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

        min_val = min(values)
        max_val = max(values)
        value_range = max_val - min_val if max_val != min_val else 1

        sparkline = []
        for value in values:
            normalized = (value - min_val) / value_range
            block_index = int(normalized * (len(blocks) - 1))
            sparkline.append(blocks[block_index])

        return "".join(sparkline)

    def generate_summary_box(
        self,
        title: str,
        metrics: Dict[str, Any]
    ) -> str:
        """
        Generate boxed summary of key metrics.

        Args:
            title: Box title
            metrics: Dictionary of metric name -> value

        Returns:
            ASCII box with metrics
        """
        # Calculate box width
        max_label_len = max(len(str(k)) for k in metrics.keys()) if metrics else 10
        box_width = max(self.width, max_label_len + 20)

        box = []
        box.append("┌" + "─" * (box_width - 2) + "┐")
        box.append("│ " + title.center(box_width - 4) + " │")
        box.append("├" + "─" * (box_width - 2) + "┤")

        for label, value in metrics.items():
            if isinstance(value, float):
                value_str = f"${value:,.2f}"
            else:
                value_str = str(value)

            line = f"│ {label:<{max_label_len}} : {value_str:>{box_width - max_label_len - 7}} │"
            box.append(line)

        box.append("└" + "─" * (box_width - 2) + "┘")

        return "\n".join(box)
