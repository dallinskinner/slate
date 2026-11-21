import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: win
    visible: true
    visibility: Window.FullScreen
    title: "Welcome to Slate"
    color: "#111214"

    // Slate tokens (same values as branding/build-kde-theme.py)
    readonly property color ink: "#111214"
    readonly property color surface: "#222327"
    readonly property color raised: "#2a2b2f"
    readonly property color text: "#e6e6e6"
    readonly property color muted: "#8a8a8a"
    readonly property color lime: "#b6f23a"
    readonly property string mono: "Hack"
    property bool showCards: false

    // pages: full welcome = setup; after an upgrade = only what's new
    readonly property var pages: backend.mode === "update"
        ? ["whatsnew"]
        : ["theme", "accent", "wallpaper", "whatsnew"].concat(backend.hasCamera ? ["camera"] : []).concat(["done"])

    Shortcut { sequence: "Esc"; onActivated: showCards ? backend.finish() : skip() }
    function skip() { backend.skipIntro(); outro.complete(); showCards = true }

    // ------------------------------------------------------------------ intro
    Item {
        id: intro
        anchors.fill: parent
        opacity: showCards ? 0 : 1
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 600; easing.type: Easing.InOutQuad } }

        MouseArea { anchors.fill: parent; onClicked: win.skip() }

        // fit the rock grid into the top ~70% of the screen
        readonly property real cell: Math.min(width * 0.92 / backend.cols / 0.602,
                                              height * 0.68 / backend.rows / 1.17)
        Column {
            id: rock
            anchors.horizontalCenter: parent.horizontalCenter
            y: parent.height * 0.08
            Repeater {
                model: backend.rows
                Text {
                    text: backend.frame[index] || ""
                    textFormat: Text.StyledText
                    font.family: win.mono
                    font.pixelSize: intro.cell
                    height: intro.cell * 1.17
                    color: win.lime
                    renderType: Text.QtRendering
                }
            }
        }

        Column {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: rock.bottom
            anchors.topMargin: parent.height * 0.03
            spacing: parent.height * 0.02
            Image {
                id: wordmark
                anchors.horizontalCenter: parent.horizontalCenter
                source: backend.logo
                sourceSize.height: win.height * 0.07
                opacity: 0
            }
            Text {
                id: versionText
                property int shown: 0
                readonly property string full: backend.version + " " + backend.releaseName
                anchors.horizontalCenter: parent.horizontalCenter
                text: full.substring(0, shown) + (shown < full.length && backend.introDone ? "_" : "")
                font.family: win.mono
                font.pixelSize: win.height * 0.03
                color: win.text
            }
        }

        SequentialAnimation {
            id: outro
            running: backend.introDone
            NumberAnimation { target: wordmark; property: "opacity"; to: 1; duration: 700 }
            NumberAnimation { target: versionText; property: "shown"; to: versionText.full.length; duration: 80 * versionText.full.length }
            PauseAnimation { duration: 1400 }
            ScriptAction { script: win.showCards = true }
        }
    }

    // ------------------------------------------------------------------ cards
    Rectangle {
        id: card
        width: Math.min(parent.width - 64, 820)
        height: Math.min(parent.height - 64, 560)
        anchors.centerIn: parent
        radius: 24
        color: win.surface
        opacity: showCards ? 1 : 0
        visible: opacity > 0
        scale: showCards ? 1 : 0.96
        Behavior on opacity { NumberAnimation { duration: 500 } }
        Behavior on scale { NumberAnimation { duration: 500; easing.type: Easing.OutCubic } }

        property int page: 0
        readonly property string kind: win.pages[page]

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 36
            spacing: 18

            Text {
                text: ({
                    theme: "Light or dark?",
                    accent: "Pick an accent color",
                    wallpaper: "Choose a wallpaper",
                    whatsnew: "What's new in " + backend.releaseName,
                    camera: "Turn on the FaceTime camera",
                    done: "You're all set"
                })[card.kind]
                color: win.text
                font.pixelSize: 30
                font.weight: Font.DemiBold
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: win.muted
                font.pixelSize: 15
                text: ({
                    theme: "You can switch any time in Quick Settings or System Settings > Colors & Themes.",
                    accent: "Used for highlights, buttons and folders.",
                    wallpaper: "Every Slate release brings a new rock. Agate, Basalt, and more to come.",
                    whatsnew: "Slate " + backend.version + " " + backend.releaseName,
                    camera: "Your Mac's camera needs a driver and Apple firmware that Slate can download now (about 5 MB). You'll need your password.",
                    done: "Open the launcher at the bottom-left, or press the Meta key. Brave is Meta+B, Files is Meta+E. Type slate in Konsole for system info."
                })[card.kind]
            }

            // --- page contents ---
            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: ["theme", "accent", "wallpaper", "whatsnew", "camera", "done"].indexOf(card.kind)

                // theme
                RowLayout {
                    spacing: 24
                    property string chosen: "dark"
                    id: themeRow
                    Repeater {
                        model: [{ id: "dark", name: "Slate Dark", img: backend.themePreviewDark },
                                { id: "light", name: "Slate Light", img: backend.themePreviewLight }]
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: width * 9 / 16
                                radius: 14
                                color: "transparent"
                                border.width: themeRow.chosen === modelData.id ? 3 : 1
                                border.color: themeRow.chosen === modelData.id ? win.lime : win.raised
                                Image {
                                    anchors.fill: parent; anchors.margins: 4
                                    source: modelData.img; fillMode: Image.PreserveAspectCrop
                                }
                                MouseArea {
                                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                    onClicked: { themeRow.chosen = modelData.id; backend.setTheme(modelData.id) }
                                }
                            }
                            Text { text: modelData.name; color: win.text; font.pixelSize: 16; Layout.alignment: Qt.AlignHCenter }
                        }
                    }
                }

                // accent
                RowLayout {
                    id: accentRow
                    spacing: 28
                    property string chosen: "#b6f23a"
                    Item { Layout.fillWidth: true }
                    Repeater {
                        model: backend.accents
                        ColumnLayout {
                            spacing: 10
                            Rectangle {
                                Layout.alignment: Qt.AlignHCenter
                                width: 88; height: 88; radius: 44
                                color: modelData.color
                                border.width: accentRow.chosen === modelData.color ? 5 : 0
                                border.color: win.text
                                MouseArea {
                                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                    onClicked: { accentRow.chosen = modelData.color; backend.setAccent(modelData.color) }
                                }
                            }
                            Text { text: modelData.name; color: win.text; font.pixelSize: 16; Layout.alignment: Qt.AlignHCenter }
                        }
                    }
                    Item { Layout.fillWidth: true }
                }

                // wallpaper
                GridView {
                    id: wpGrid
                    clip: true
                    cellWidth: width / 4
                    cellHeight: cellWidth * 0.72
                    model: backend.wallpapers
                    property string chosen: ""
                    delegate: Item {
                        width: wpGrid.cellWidth; height: wpGrid.cellHeight
                        Rectangle {
                            anchors.fill: parent; anchors.margins: 6
                            radius: 12
                            color: "transparent"
                            border.width: wpGrid.chosen === modelData.path ? 3 : 1
                            border.color: wpGrid.chosen === modelData.path ? win.lime : win.raised
                            Image {
                                anchors.fill: parent; anchors.margins: 3; anchors.bottomMargin: 24
                                source: modelData.thumb; fillMode: Image.PreserveAspectCrop
                            }
                            Text {
                                anchors.bottom: parent.bottom; anchors.bottomMargin: 4
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: modelData.name; color: win.muted; font.pixelSize: 12
                            }
                            MouseArea {
                                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                onClicked: { wpGrid.chosen = modelData.path; backend.setWallpaper(modelData.path) }
                            }
                        }
                    }
                }

                // what's new
                ColumnLayout {
                    spacing: 16
                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        Text {
                            width: card.width - 72
                            text: backend.whatsNew
                            textFormat: Text.MarkdownText
                            wrapMode: Text.WordWrap
                            color: win.text
                            font.pixelSize: 15
                        }
                    }
                    SlateButton {
                        id: useRock
                        text: "Use the " + backend.releaseName + " wallpaper"
                        onClicked: { backend.setWallpaper(backend.currentRockWallpaper); text = "Wallpaper set" }
                    }
                }

                // camera
                ColumnLayout {
                    spacing: 16
                    SlateButton {
                        enabled: backend.status === "" || backend.status === "failed"
                        text: backend.status === "installing" ? "Installing..."
                            : backend.status === "done" ? "Camera enabled. Restart to use it"
                            : backend.status === "failed" ? "That didn't work. Try again"
                            : "Enable the camera"
                        onClicked: backend.installCamera()
                    }
                    Item { Layout.fillHeight: true }
                }

                // done
                Item {
                    Image {
                        anchors.centerIn: parent
                        source: backend.logo
                        sourceSize.height: 70
                        opacity: 0.9
                    }
                }
            }

            // --- navigation ---
            RowLayout {
                Layout.fillWidth: true
                Row {
                    spacing: 8
                    visible: win.pages.length > 1
                    Repeater {
                        model: win.pages.length
                        Rectangle {
                            width: index === card.page ? 22 : 8; height: 8; radius: 4
                            color: index === card.page ? win.lime : win.raised
                            Behavior on width { NumberAnimation { duration: 200 } }
                        }
                    }
                }
                Item { Layout.fillWidth: true }
                SlateButton {
                    flat: true
                    visible: card.page > 0
                    text: "Back"
                    onClicked: card.page--
                }
                SlateButton {
                    text: card.page === win.pages.length - 1 ? "Start using Slate" : "Next"
                    onClicked: card.page === win.pages.length - 1 ? backend.finish() : card.page++
                }
            }
        }
    }

    Component.onCompleted: if (backend.startPage >= 0) { skip(); card.page = backend.startPage }
}
