// Slate splash shown while Plasma starts after login (based on Breeze's Splash.qml).
import QtQuick
import org.kde.kirigami 2 as Kirigami

Rectangle {
    id: root
    color: "#1a1b1e"

    property int stage

    onStageChanged: {
        if (stage == 2) {
            fadeIn.running = true;
        }
    }

    Item {
        id: content
        anchors.fill: parent
        opacity: 0

        Image {
            id: logo
            anchors.centerIn: parent
            asynchronous: true
            source: "images/slate-wordmark.png"
            fillMode: Image.PreserveAspectFit
            width: Math.min(parent.width * 0.3, sourceSize.width)
        }

        // lime dot that pulses under the wordmark while loading
        Rectangle {
            id: dot
            width: Kirigami.Units.gridUnit * 0.6
            height: width
            radius: width / 2
            color: "#b6f23a"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: logo.bottom
            anchors.topMargin: Kirigami.Units.gridUnit * 2
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                running: Kirigami.Units.longDuration > 1
                NumberAnimation { from: 1; to: 0.2; duration: 700; easing.type: Easing.InOutQuad }
                NumberAnimation { from: 0.2; to: 1; duration: 700; easing.type: Easing.InOutQuad }
            }
        }
    }

    OpacityAnimator {
        id: fadeIn
        running: false
        target: content
        from: 0
        to: 1
        duration: Kirigami.Units.veryLongDuration * 2
        easing.type: Easing.InOutQuad
    }
}
