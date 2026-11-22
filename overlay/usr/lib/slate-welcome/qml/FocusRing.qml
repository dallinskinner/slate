import QtQuick

// Keyboard focus outline for Slate Welcome tiles and buttons
Rectangle {
    property Item target: parent
    property real gap: 5
    anchors.fill: parent
    anchors.margins: -gap
    radius: (target && target.radius !== undefined ? target.radius : 8) + gap
    color: "transparent"
    border.width: 2
    border.color: "#e6e6e6"
    visible: false
}
