import QtQuick
import QtQuick.Controls

// Pill button in Slate colors: lime with dark text, or flat (text only)
AbstractButton {
    id: b
    property bool flat: false
    implicitWidth: label.implicitWidth + 44
    implicitHeight: 44
    hoverEnabled: true
    opacity: enabled ? 1 : 0.5
    background: Rectangle {
        radius: height / 2
        color: b.flat ? (b.hovered ? "#2a2b2f" : "transparent")
                      : (b.down ? "#92d630" : b.hovered ? "#ccf778" : "#b6f23a")
    }
    contentItem: Text {
        id: label
        text: b.text
        color: b.flat ? "#e6e6e6" : "#111214"
        font.pixelSize: 15
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
