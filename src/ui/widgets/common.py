"""
Reusable form widget components for CommerceCalc.
"""
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QDoubleSpinBox, QSpinBox,
    QComboBox, QHBoxLayout, QVBoxLayout, QFrame, QPushButton,
    QCheckBox, QToolButton, QSizePolicy, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QIcon
from ...core.money import to_decimal, money as fmt_money


class FormFieldRow(QWidget):
    """A labeled input row with optional tooltip."""
    value_changed = Signal()

    def __init__(self, label: str, input_widget: QWidget,
                 tooltip: str = "", required: bool = False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        # Label
        lbl = QLabel(label + ("*" if required else ""))
        lbl.setObjectName("form_label")
        lbl.setFixedWidth(200)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if tooltip:
            lbl.setToolTip(tooltip)

        layout.addWidget(lbl)
        layout.addWidget(input_widget, 1)

        if tooltip:
            info_btn = QPushButton("?")
            info_btn.setFixedSize(20, 20)
            info_btn.setToolTip(tooltip)
            info_btn.setObjectName("secondary_btn")
            layout.addWidget(info_btn)


class MoneyInput(QDoubleSpinBox):
    """Currency input widget, INR-focused."""

    def __init__(self, parent=None, prefix="₹ ", max_val=9999999.99):
        super().__init__(parent)
        self.setPrefix(prefix)
        self.setDecimals(2)
        self.setMinimum(0.0)
        self.setMaximum(max_val)
        self.setSingleStep(1.0)
        self.setGroupSeparatorShown(True)
        self.setMinimumWidth(160)

    def get_decimal(self) -> Decimal:
        return to_decimal(str(self.value()))

    def set_decimal(self, value: Decimal):
        self.setValue(float(value))


class PercentInput(QDoubleSpinBox):
    """Percentage input widget (0-100%)."""

    def __init__(self, parent=None, max_val=100.0):
        super().__init__(parent)
        self.setSuffix(" %")
        self.setDecimals(2)
        self.setMinimum(0.0)
        self.setMaximum(max_val)
        self.setSingleStep(0.5)
        self.setMinimumWidth(120)

    def get_decimal(self) -> Decimal:
        return to_decimal(str(self.value()))


class MetricCard(QFrame):
    """A single KPI/metric display card."""

    def __init__(self, label: str, value: str = "₹0.00",
                 card_type: str = "default",  # default, success, danger
                 sublabel: str = "", parent=None):
        super().__init__(parent)
        object_names = {
            "default": "metric_card",
            "success": "metric_card_success",
            "danger": "metric_card_danger",
        }
        self.setObjectName(object_names.get(card_type, "metric_card"))
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self._label = QLabel(label.upper())
        self._label.setObjectName("metric_label")

        value_obj = "metric_value"
        if card_type == "success":
            value_obj = "metric_value_positive"
        elif card_type == "danger":
            value_obj = "metric_value_negative"

        self._value = QLabel(value)
        self._value.setObjectName(value_obj)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self._value.setFont(font)

        layout.addWidget(self._label)
        layout.addWidget(self._value)

        if sublabel:
            self._sub = QLabel(sublabel)
            self._sub.setObjectName("metric_label")
            layout.addWidget(self._sub)

    def update_value(self, value: str, card_type: str = None):
        self._value.setText(value)
        if card_type:
            obj_map = {"default": "metric_value", "success": "metric_value_positive",
                       "danger": "metric_value_negative"}
            self._value.setObjectName(obj_map.get(card_type, "metric_value"))
            self._value.style().unpolish(self._value)
            self._value.style().polish(self._value)


class SectionTitle(QLabel):
    """A styled section title label."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("section_title")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.setFont(font)


class Divider(QFrame):
    """A horizontal divider line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setFixedHeight(1)


class ResultRow(QWidget):
    """A labeled result display row (label + value)."""

    def __init__(self, label: str, value: str = "–",
                 color: str = None, bold: bool = False,
                 tooltip: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setObjectName("form_label")
        if tooltip:
            lbl.setToolTip(tooltip)
        lbl.setWordWrap(True)

        self._value_lbl = QLabel(value)
        font = QFont()
        if bold:
            font.setBold(True)
            font.setPointSize(13)
        if color:
            palette = self._value_lbl.palette()
            palette.setColor(QPalette.WindowText, QColor(color))
            self._value_lbl.setPalette(palette)
        if bold or color:
            self._value_lbl.setFont(font)

        self._value_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(lbl, 2)
        layout.addWidget(self._value_lbl, 1)

    def set_value(self, value: str, color: str = None):
        self._value_lbl.setText(value)
        if color:
            palette = self._value_lbl.palette()
            palette.setColor(QPalette.WindowText, QColor(color))
            self._value_lbl.setPalette(palette)


class DisclaimerBox(QFrame):
    """Shows a disclaimer/warning message."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("disclaimer_box")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        icon = QLabel("⚠")
        icon.setStyleSheet("color: #f59e0b; font-size: 16px;")
        icon.setFixedWidth(24)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #a16207; font-size: 11px;")

        layout.addWidget(icon)
        layout.addWidget(lbl, 1)


class InfoBox(QFrame):
    """Shows an informational message."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("info_box")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        icon = QLabel("ℹ")
        icon.setStyleSheet("color: #60a5fa; font-size: 16px;")
        icon.setFixedWidth(24)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #93c5fd; font-size: 11px;")

        layout.addWidget(icon)
        layout.addWidget(lbl, 1)


def make_card(title: str = None) -> tuple[QFrame, QVBoxLayout]:
    """Create a styled card frame with a layout. Returns (frame, layout)."""
    card = QFrame()
    card.setObjectName("card")
    card.setFrameShape(QFrame.StyledPanel)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 16, 20, 20)
    layout.setSpacing(12)
    if title:
        title_lbl = SectionTitle(title)
        layout.addWidget(title_lbl)
        layout.addWidget(Divider())
    return card, layout


def fmt_inr(value, show_sign: bool = False) -> str:
    """Format a Decimal value as INR currency string."""
    d = to_decimal(value)
    formatted = f"₹{abs(d):,.2f}"
    if show_sign:
        if d < 0:
            return f"−{formatted}"
        elif d > 0:
            return f"+{formatted}"
    return formatted if d >= 0 else f"−₹{abs(d):,.2f}"


def fmt_pct(value) -> str:
    """Format as percentage."""
    return f"{to_decimal(value):.2f}%"
