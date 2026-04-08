import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1040
    height: 760
    visible: true
    title: "Empire Prototype"
    color: currentScreen === "menu" ? "#d7cbb7" : "#e8e1d4"

    readonly property var emptyState: ({
        "map": {"width": 0, "height": 0},
        "turn": {"number": 0, "current_player": 0},
        "selected_unit_id": null,
        "last_event": "",
        "game_over": false,
        "winner_id": null,
        "legal_targets": [],
        "pending_move_target": null,
        "preview_path": [],
        "preview_full_path": [],
        "preview_reachable_path": [],
        "preview_stop_position": null,
        "preview_reaches_target": false,
        "tiles": [],
        "units": []
    })
    readonly property var emptyMovementAnimation: ({
        "active": false,
        "unit_id": -1,
        "unit_type": "",
        "owner_id": -1,
        "origin": null,
        "path": [],
        "duration_ms": 0
    })
    readonly property var themeLibrary: ({
        "classicFlat": {
            "useTerrainImages": false,
            "terrainSources": {},
            "terrainFallbackColors": {
                "plains": "#d9c7a4",
                "forest": "#8aa05b",
                "mountain": "#8d8a84",
                "water": "#6a9fb5",
                "city": "#d8b26e"
            }
        },
        "empireDeluxe": {
            "useTerrainImages": true,
            "terrainSources": {
                "plains": "../assets/themes/empire-deluxe/terrain/plains.svg",
                "forest": "../assets/themes/empire-deluxe/terrain/forest.svg",
                "mountain": "../assets/themes/empire-deluxe/terrain/mountain.svg",
                "water": "../assets/themes/empire-deluxe/terrain/water.svg",
                "shore": "../assets/themes/empire-deluxe/terrain/shore.svg",
                "city": "../assets/themes/empire-deluxe/terrain/city.svg"
            },
            "terrainFallbackColors": {
                "plains": "#d8c79a",
                "forest": "#7f9a54",
                "mountain": "#8d8a84",
                "water": "#6a9fb5",
                "city": "#d8b26e"
            }
        }
    })
    property string activeThemeId: (typeof gameController !== "undefined" && gameController) ? gameController.activeThemeId : "empireDeluxe"
    property var gameState: (typeof gameController !== "undefined" && gameController) ? gameController.state : emptyState
    property var movementAnimation: (typeof gameController !== "undefined" && gameController) ? gameController.movementAnimation : emptyMovementAnimation
    property real movementProgress: 0
    property bool movementTweenInternalStop: false
    property int selectedUnitId: (gameState && gameState.selected_unit_id !== undefined && gameState.selected_unit_id !== null)
                                 ? gameState.selected_unit_id
                                 : -1
    property string currentScreen: "menu"
    property string selectedScenarioId: (typeof gameController !== "undefined" && gameController) ? gameController.selectedScenarioId : "classic"
    property string hoverInfo: ""

    Connections {
        target: gameController

        function onStateChanged() {
            root.gameState = gameController.state
        }

        function onMovementAnimationChanged() {
            if (movementAnimation && movementAnimation.active && movementAnimation.path && movementAnimation.path.length > 0) {
                movementProgress = 0
                movementTweenInternalStop = true
                movementTween.stop()
                movementTween.from = 0
                movementTween.to = movementAnimation.path.length
                movementTween.duration = movementAnimation.duration_ms || 0
                movementTween.start()
                movementTweenInternalStop = false
            } else {
                movementTweenInternalStop = true
                movementTween.stop()
                movementProgress = 0
                movementTweenInternalStop = false
            }
        }

        function onSelectedScenarioChanged() {
            root.selectedScenarioId = gameController.selectedScenarioId
        }

        function onActiveThemeChanged() {
            root.activeThemeId = gameController.activeThemeId
        }
    }

    NumberAnimation {
        id: movementTween
        target: root
        property: "movementProgress"
        from: 0
        to: 0
        duration: 0
        easing.type: Easing.InOutQuad
        onStopped: {
            if (!movementTweenInternalStop && movementAnimation && movementAnimation.active && typeof gameController !== "undefined" && gameController) {
                gameController.clearMovementAnimation()
            }
        }
    }

    header: currentScreen === "game" ? gameHeader : null

    ToolBar {
        id: gameHeader
        contentHeight: 56

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.rightMargin: 20
            spacing: 18

            Label {
                text: "Empire"
                font.pixelSize: 28
                font.family: "Serif"
                color: "#17324d"
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#17324d"
                opacity: 0.25
            }

            Label {
                text: gameState.game_over
                      ? "Winner: Player " + gameState.winner_id
                      : "Turn " + gameState.turn.number + " / Player " + gameState.turn.current_player
                font.pixelSize: 18
                color: "#17324d"
            }

            Button {
                text: "Menu"
                onClicked: root.currentScreen = "menu"
            }

            Button {
                text: "Save"
                onClicked: gameController.saveGame()
            }

            Button {
                text: "Load"
                onClicked: {
                    gameController.loadGame()
                    root.currentScreen = "game"
                }
            }

            Button {
                text: "End Turn"
                enabled: !gameState.game_over
                onClicked: gameController.endTurn()
            }
        }
    }

    Item {
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent
            visible: currentScreen === "menu"
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#efe3cf" }
                GradientStop { position: 1.0; color: "#c5b18d" }
            }

            Rectangle {
                anchors.fill: parent
                color: "transparent"
                border.color: "#8d7651"
                border.width: 18
            }

            ColumnLayout {
                anchors.centerIn: parent
                width: 420
                spacing: 18

                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Empire"
                    font.pixelSize: 64
                    font.family: "Serif"
                    color: "#17324d"
                }

                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    text: "Rundenbasiertes Strategie-Prototyping mit getrennten Engine- und QML-Schichten."
                    color: "#274867"
                    font.pixelSize: 18
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 360
                    radius: 20
                    color: "#f5ede0"
                    border.color: "#aa8d63"
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 24
                        spacing: 14

                        Button {
                            Layout.fillWidth: true
                            text: "Spiel starten"
                            font.pixelSize: 22
                            onClicked: {
                                gameController.startNewGame()
                                root.currentScreen = "game"
                            }
                        }

                        Button {
                            Layout.fillWidth: true
                            text: "Spiel laden"
                            onClicked: {
                                gameController.loadGame()
                                root.currentScreen = "game"
                            }
                        }

                        Button {
                            Layout.fillWidth: true
                            text: "Einstellungen"
                            enabled: false
                        }

                        Label {
                            Layout.fillWidth: true
                            text: "Szenario"
                            color: "#17324d"
                            font.bold: true
                        }

                        ComboBox {
                            id: scenarioBox
                            Layout.fillWidth: true
                            model: (typeof gameController !== "undefined" && gameController) ? gameController.scenarios : []
                            textRole: "name"
                            valueRole: "id"
                            currentIndex: scenarioIndexForId(selectedScenarioId)

                            onActivated: {
                                const scenario = model[currentIndex]
                                if (scenario) {
                                    gameController.setSelectedScenario(scenario.id)
                                }
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: selectedScenarioDescription()
                            color: "#5b4b37"
                        }

                        Label {
                            Layout.fillWidth: true
                            text: "Grafik-Theme"
                            color: "#17324d"
                            font.bold: true
                        }

                        ComboBox {
                            id: themeBox
                            Layout.fillWidth: true
                            model: themeOptions()
                            textRole: "name"
                            valueRole: "id"
                            currentIndex: themeIndexForId(activeThemeId)

                            onActivated: {
                                const theme = model[currentIndex]
                                if (theme) {
                                    gameController.setActiveThemeId(theme.id)
                                }
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: selectedThemeDescription()
                            color: "#5b4b37"
                        }

                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: "Aktuell verfügbar: neues Spiel starten und Quick-Load aus "
                                  + ((typeof gameController !== "undefined" && gameController) ? gameController.saveDisplayPath : "saves/quicksave.json")
                            color: "#5b4b37"
                        }
                    }
                }
            }
        }

        RowLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 20
            visible: currentScreen === "game"

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 18
                color: "#f6f1e8"
                border.color: "#c7baa5"
                border.width: 1

                Flickable {
                    anchors.fill: parent
                    anchors.margins: 18
                    contentWidth: boardPixelWidth()
                    contentHeight: boardPixelHeight()
                    clip: true

                    Grid {
                        id: board
                        columns: gameState.map.width
                        spacing: 4

                        Repeater {
                            model: gameState.map.width * gameState.map.height

                            delegate: Rectangle {
                                required property int index

                                property int cellX: index % gameState.map.width
                                property int cellY: Math.floor(index / gameState.map.width)
                                property var tileData: findTile(cellX, cellY)
                                property var occupant: findMapUnit(cellX, cellY)
                                property bool animatedUnitHidden: isMovementAnimationUnit(occupant)
                                property var displayedOccupant: animatedUnitHidden ? null : occupant
                                property var legalTarget: findLegalTarget(cellX, cellY)
                                property bool tileVisible: tileData && tileData.visible
                                property bool tileExplored: tileData && tileData.explored
                                property bool coastalWaterTile: tileVisible && isCoastalWaterTile(cellX, cellY)

                                width: 30
                                height: 30
                                radius: 8
                                    clip: true
                                    color: tileVisible
                                        ? terrainFallbackColor(tileData ? tileData.terrain : "plains")
                                        : (tileExplored ? "#5e615d" : "#1f2730")
                                border.width: selectedUnitId >= 0 && displayedOccupant && displayedOccupant.id === selectedUnitId ? 3 : 1
                                border.color: selectedUnitId >= 0 && displayedOccupant && displayedOccupant.id === selectedUnitId ? "#8b1e3f" : (tileVisible ? "#9b8866" : "#39414a")

                                    Image {
                                     anchors.fill: parent
                                     visible: tileVisible && themeUsesTerrainImages()
                                        source: terrainSourceForTile(tileData, cellX, cellY)
                                     fillMode: Image.Stretch
                                     smooth: true
                                     opacity: tileExplored ? 0.95 : 1.0
                                    }

                                    Image {
                                        anchors.fill: parent
                                    visible: coastalWaterTile && themeUsesTerrainImages()
                                        source: terrainSource("shore")
                                        fillMode: Image.Stretch
                                        smooth: true
                                        opacity: 0.95
                                    }

                                Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: 6
                                    radius: 6
                                    color: legalTarget ? legalTargetColor(legalTarget.action_type) : "transparent"
                                    opacity: legalTarget ? 0.85 : 0.0
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    radius: 5
                                    color: isPreviewReachableStep(cellX, cellY) ? "#fff4a3" : (isPreviewFullStep(cellX, cellY) ? "#f3df9d" : "transparent")
                                    opacity: isPreviewReachableStep(cellX, cellY) ? 0.7 : (isPreviewFullStep(cellX, cellY) ? 0.35 : 0.0)
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    radius: 6
                                    color: "transparent"
                                    border.width: isPendingMoveTarget(cellX, cellY)
                                                  ? 4
                                                  : (isQueuedOrderTarget(cellX, cellY)
                                                     ? 3
                                                     : (isPreviewTarget(cellX, cellY) ? 2 : (isPreviewStop(cellX, cellY) ? 2 : 0)))
                                    border.color: isPendingMoveTarget(cellX, cellY)
                                                  ? "#f6f1e8"
                                                  : (isQueuedOrderTarget(cellX, cellY)
                                                     ? "#8dd8ff"
                                                     : (isPreviewTarget(cellX, cellY) ? "#fff4a3" : "#e18b5a"))
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: 1
                                    radius: 8
                                    color: "transparent"
                                    border.width: isPendingMoveTarget(cellX, cellY) || isQueuedOrderTarget(cellX, cellY) ? 1 : 0
                                    border.color: isPendingMoveTarget(cellX, cellY) ? "#17324d" : "#c9f0ff"
                                    opacity: isPendingMoveTarget(cellX, cellY) ? 0.95 : 0.7
                                }

                                Rectangle {
                                    visible: isPreviewStop(cellX, cellY)
                                    width: 8
                                    height: 8
                                    radius: 4
                                    anchors.centerIn: parent
                                    color: "#e18b5a"
                                }

                                Rectangle {
                                    visible: targetBadgeText(cellX, cellY) !== ""
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    anchors.bottom: parent.bottom
                                    anchors.bottomMargin: 2
                                    radius: 5
                                    height: 12
                                    width: targetBadgeLabel.implicitWidth + 8
                                    color: targetBadgeColor(cellX, cellY)
                                    opacity: 0.92

                                    Text {
                                        id: targetBadgeLabel
                                        anchors.centerIn: parent
                                        text: targetBadgeText(cellX, cellY)
                                        color: "#f6f1e8"
                                        font.pixelSize: 8
                                        font.bold: true
                                    }
                                }

                                Item {
                                    anchors.centerIn: parent
                                    width: 22
                                    height: 22
                                    opacity: tileVisible ? 1.0 : (tileExplored ? 0.55 : 0.0)
                                    visible: displayedOccupant || hasCityIcon(tileData)

                                    Image {
                                        anchors.centerIn: parent
                                        width: 18
                                        height: 18
                                        source: displayedOccupant ? unitIconSource(displayedOccupant.unit_type) : cityIconSource()
                                        fillMode: Image.PreserveAspectFit
                                        smooth: true
                                    }

                                    Rectangle {
                                        visible: ownerBadgeText(displayedOccupant, tileData) !== ""
                                        width: 11
                                        height: 11
                                        radius: 5.5
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        color: displayedOccupant ? ownerBadgeColor(displayedOccupant.owner_id) : ownerBadgeColor(tileData.city_owner_id)
                                        border.color: "#f6f1e8"
                                        border.width: 1

                                        Text {
                                            anchors.centerIn: parent
                                            text: ownerBadgeText(displayedOccupant, tileData)
                                            color: "#f6f1e8"
                                            font.pixelSize: 8
                                            font.bold: true
                                        }
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    enabled: tileVisible
                                    hoverEnabled: true
                                    onEntered: {
                                        hoverInfo = describeTile(cellX, cellY, tileData, displayedOccupant, legalTarget)
                                        if (selectedUnitId >= 0) {
                                            gameController.setPreviewTarget(cellX, cellY)
                                        }
                                    }
                                    onExited: {
                                        if (hoverInfo === describeTile(cellX, cellY, tileData, displayedOccupant, legalTarget)) {
                                            hoverInfo = ""
                                        }
                                        gameController.clearPreviewTarget()
                                    }
                                    onClicked: {
                                        if (legalTarget && selectedUnitId >= 0) {
                                            gameController.moveUnit(selectedUnitId, cellX, cellY)
                                        } else if (selectedUnitId >= 0 && !occupant) {
                                            if (isPendingMoveTarget(cellX, cellY)) {
                                                gameController.moveUnit(selectedUnitId, cellX, cellY)
                                            } else {
                                                gameController.setPendingMoveTarget(selectedUnitId, cellX, cellY)
                                            }
                                        } else if (displayedOccupant) {
                                            gameController.selectUnit(displayedOccupant.id)
                                        }
                                    }
                                }
                            }
                        }

                        Item {
                            id: movementLayer
                            width: boardPixelWidth()
                            height: boardPixelHeight()
                            visible: movementAnimation.active && movementAnimation.path && movementAnimation.path.length > 0
                            z: 10

                            Item {
                                visible: movementLayer.visible
                                width: 22
                                height: 22
                                x: movementGhostLeft()
                                y: movementGhostTop()
                                opacity: 0.96

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 11
                                    color: movementGhostColor()
                                    border.width: 2
                                    border.color: "#f6f1e8"
                                }

                                Image {
                                    anchors.centerIn: parent
                                    width: 18
                                    height: 18
                                    source: movementAnimation.unit_type ? unitIconSource(movementAnimation.unit_type) : ""
                                    fillMode: Image.PreserveAspectFit
                                    smooth: true
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.preferredWidth: 340
                Layout.maximumWidth: 360
                Layout.fillHeight: true
                radius: 18
                color: "#17324d"

                ScrollView {
                    id: sideScroll
                    anchors.fill: parent
                    anchors.margins: 12
                    clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical.policy: ScrollBar.AsNeeded

                    ColumnLayout {
                        width: sideScroll.availableWidth
                        spacing: 16

                        Rectangle {
                            Layout.fillWidth: true
                            radius: 16
                            color: "#1f3a57"
                            border.color: "#466684"
                            border.width: 1
                            implicitHeight: statusColumn.implicitHeight + 24

                            Column {
                                id: statusColumn
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 8

                                Rectangle {
                                    visible: movementAnimation && movementAnimation.active && movementAnimation.path && movementAnimation.path.length > 0
                                    width: parent.width
                                    radius: 12
                                    color: "#274867"
                                    border.color: "#6b92b3"
                                    border.width: 1
                                    implicitHeight: movementColumn.implicitHeight + 24

                                    Column {
                                        id: movementColumn
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        spacing: 6

                                        Text {
                                            text: "Movement"
                                            font.pixelSize: 18
                                            color: "#f6f1e8"
                                            font.bold: true
                                        }

                                        Text {
                                            width: parent.width
                                            wrapMode: Text.WordWrap
                                            text: movementSummary()
                                            color: "#d9c7a4"
                                        }
                                    }
                                }

                                Text {
                                    text: "Status"
                                    font.pixelSize: 24
                                    color: "#f6f1e8"
                                }

                                Text {
                                    visible: gameState.game_over
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    text: gameState.game_over ? "Game Over. Player " + gameState.winner_id + " wins." : ""
                                    color: "#f1dfb0"
                                    font.bold: true
                                }

                                Text {
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    text: (typeof gameController !== "undefined" && gameController) ? gameController.commandMessage : ""
                                    color: "#d9c7a4"
                                }

                                Text {
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    text: "Quick Save: "
                                          + ((typeof gameController !== "undefined" && gameController) ? gameController.saveDisplayPath : "saves/quicksave.json")
                                    color: "#9fb7d0"
                                    font.pixelSize: 12
                                }

                                Rectangle {
                                    width: parent.width
                                    height: 1
                                    color: "#6e8aa8"
                                    opacity: 0.35
                                }

                                Text {
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    text: gameState.last_event
                                    color: "#f6f1e8"
                                }

                                Text {
                                    width: parent.width
                                    text: "Theme: " + selectedThemeDescription()
                                    color: "#d9c7a4"
                                    font.pixelSize: 12
                                }

                                ComboBox {
                                    width: parent.width
                                    model: themeOptions()
                                    textRole: "name"
                                    valueRole: "id"
                                    currentIndex: themeIndexForId(activeThemeId)

                                    onActivated: {
                                        const theme = model[currentIndex]
                                        if (theme) {
                                            gameController.setActiveThemeId(theme.id)
                                        }
                                    }
                                }

                                Text {
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    text: selectedUnitHeadline()
                                    color: selectedUnitId >= 0 ? "#f6f1e8" : "#d9c7a4"
                                    font.bold: selectedUnitId >= 0
                                }

                                Text {
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    text: selectedUnitId >= 0 ? selectedTargetSummary() : "Select a unit to see legal actions"
                                    color: "#d9c7a4"
                                }

                                Button {
                                    visible: selectedUnitHasOrders()
                                    text: "Clear Orders"
                                    onClicked: {
                                        if (selectedUnitId >= 0) {
                                            gameController.clearUnitOrders(selectedUnitId)
                                        }
                                    }
                                }

                                Button {
                                    visible: selectedUnitId >= 0 && !!gameState.pending_move_target
                                    text: "Clear Target"
                                    onClicked: {
                                        if (selectedUnitId >= 0) {
                                            gameController.clearPendingMoveTarget(selectedUnitId)
                                        }
                                    }
                                }

                                Text {
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    text: previewSummary()
                                    color: "#f1dfb0"
                                    font.pixelSize: 12
                                    visible: previewSummary() !== ""
                                }

                                Text {
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    text: hoverInfo !== "" ? hoverInfo : "Hover a visible tile for details"
                                    color: "#f1dfb0"
                                    font.pixelSize: 12
                                }

                                Text {
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    text: "Vision: bright visible, gray explored, dark unknown"
                                    color: "#9fb7d0"
                                    font.pixelSize: 12
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#d9c7a4"
                            opacity: 0.3
                        }

                        Label {
                            text: "Legend"
                            font.pixelSize: 20
                            color: "#f6f1e8"
                            font.bold: true
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            radius: 12
                            color: "#274867"
                            border.color: "#49698a"
                            border.width: 1
                            implicitHeight: legendColumn.implicitHeight + 24

                            Column {
                                id: legendColumn
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 8

                                Row {
                                    spacing: 8
                                    Rectangle { width: 14; height: 14; radius: 4; color: "#e8cf54" }
                                    Text { text: "Move"; color: "#d9c7a4" }
                                }

                                Row {
                                    spacing: 8
                                    Rectangle { width: 14; height: 14; radius: 4; color: "#c84c4c" }
                                    Text { text: "Attack"; color: "#d9c7a4" }
                                }

                                Row {
                                    spacing: 8
                                    Rectangle { width: 14; height: 14; radius: 4; color: "#8167d8" }
                                    Text { text: "Embark"; color: "#d9c7a4" }
                                }

                                Row {
                                    spacing: 8
                                    Rectangle { width: 14; height: 14; radius: 4; color: "#2e9d8f" }
                                    Text { text: "Disembark"; color: "#d9c7a4" }
                                }

                                Row {
                                    spacing: 8
                                    Rectangle {
                                        width: 14
                                        height: 14
                                        radius: 4
                                        color: "transparent"
                                        border.width: 3
                                        border.color: "#f6f1e8"
                                    }
                                    Text { text: "Pending target"; color: "#d9c7a4" }
                                }

                                Row {
                                    spacing: 8
                                    Rectangle {
                                        width: 14
                                        height: 14
                                        radius: 4
                                        color: "transparent"
                                        border.width: 3
                                        border.color: "#8dd8ff"
                                    }
                                    Text { text: "Queued orders"; color: "#d9c7a4" }
                                }

                                Row {
                                    spacing: 8
                                    Rectangle { width: 14; height: 14; radius: 7; color: "#e18b5a" }
                                    Text { text: "Stop this turn"; color: "#d9c7a4" }
                                }
                            }
                        }

                        Label {
                            text: "Cities"
                            font.pixelSize: 20
                            color: "#f6f1e8"
                            font.bold: true
                        }

                        Repeater {
                            model: ownedCities()

                            delegate: Rectangle {
                                required property var modelData

                                Layout.fillWidth: true
                                radius: 12
                                color: "#274867"
                                border.color: "#49698a"
                                border.width: 1
                                implicitHeight: cityColumn.implicitHeight + 24

                                Column {
                                    id: cityColumn
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 6

                                    Text {
                                        text: roleLabel(modelData.city_role) + " " + modelData.position.x + ", " + modelData.position.y
                                        color: "#f6f1e8"
                                        font.bold: true
                                    }

                                    Text {
                                        text: "Production " + modelData.production_points + " | Build " + (modelData.build_choice || "infantry")
                                        color: "#d9c7a4"
                                    }

                                    ComboBox {
                                        width: parent.width
                                        model: modelData.available_build_options || []
                                        currentIndex: cityBuildIndex(modelData.build_choice, modelData.available_build_options || [])

                                        onActivated: {
                                            const unitType = model[currentIndex]
                                            if (unitType) {
                                                gameController.setCityProduction(modelData.position.x, modelData.position.y, unitType)
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#d9c7a4"
                            opacity: 0.3
                        }

                        Label {
                            text: "Units"
                            font.pixelSize: 20
                            color: "#f6f1e8"
                            font.bold: true
                        }

                        Repeater {
                            model: gameState.units

                            delegate: Rectangle {
                                required property var modelData

                                Layout.fillWidth: true
                                radius: 12
                                color: modelData.id === selectedUnitId ? "#8b1e3f" : "#274867"
                                border.color: modelData.id === selectedUnitId ? "#d19ab0" : "#49698a"
                                border.width: 1
                                implicitHeight: unitColumn.implicitHeight + 24

                                Column {
                                    id: unitColumn
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 6

                                    Row {
                                        width: parent.width
                                        spacing: 8

                                        Image {
                                            width: 18
                                            height: 18
                                            source: unitIconSource(modelData.unit_type)
                                            fillMode: Image.PreserveAspectFit
                                        }

                                        Text {
                                            text: modelData.unit_type + " #" + modelData.id
                                            color: "#f6f1e8"
                                            font.bold: true
                                        }
                                    }

                                    Text {
                                        text: "Owner " + modelData.owner_id + " | HP " + modelData.hp + "/" + modelData.max_hp
                                        color: "#d9c7a4"
                                    }

                                    Text {
                                        text: "Pos " + modelData.position.x + ", " + modelData.position.y + " | Move " + modelData.moves_remaining + "/" + modelData.max_moves
                                        color: "#d9c7a4"
                                    }

                                    Text {
                                        text: modelData.domain + " | ATK " + modelData.attack + " DEF " + modelData.defense
                                        color: "#d9c7a4"
                                    }

                                    Text {
                                        text: "Range " + modelData.attack_range
                                        color: "#d9c7a4"
                                    }

                                    Text {
                                        width: parent.width
                                        wrapMode: Text.WordWrap
                                        text: (modelData.embarked_in !== undefined && modelData.embarked_in !== null)
                                              ? "Embarked in #" + modelData.embarked_in
                                              : (modelData.cargo_capacity > 0
                                                 ? "Cargo " + modelData.cargo_count + "/" + modelData.cargo_capacity + cargoLabel(modelData.cargo_unit_ids)
                                                 : "No cargo")
                                        color: "#d9c7a4"
                                    }

                                    Text {
                                        width: parent.width
                                        wrapMode: Text.WordWrap
                                        visible: modelData.queued_destination !== undefined && modelData.queued_destination !== null
                                        text: visible
                                              ? "Orders " + modelData.queued_destination.x + ", " + modelData.queued_destination.y
                                              : ""
                                        color: "#f1dfb0"
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: gameController.selectUnit(modelData.id)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    function boardStep() {
        return 34
    }

    function boardCellSize() {
        return 30
    }

    function boardGap() {
        return boardStep() - boardCellSize()
    }

    function boardPixelWidth() {
        if (!gameState.map || gameState.map.width <= 0) {
            return 0
        }
        return gameState.map.width * boardCellSize() + Math.max(0, gameState.map.width - 1) * boardGap()
    }

    function boardPixelHeight() {
        if (!gameState.map || gameState.map.height <= 0) {
            return 0
        }
        return gameState.map.height * boardCellSize() + Math.max(0, gameState.map.height - 1) * boardGap()
    }

    function boardTileTopLeft(position) {
        return {
            "x": position.x * boardStep(),
            "y": position.y * boardStep()
        }
    }

    function movementGhostPosition() {
        if (!movementAnimation || !movementAnimation.active || !movementAnimation.origin || !movementAnimation.path || movementAnimation.path.length === 0) {
            return null
        }

        const path = movementAnimation.path
        const clampedProgress = Math.max(0, Math.min(movementProgress, path.length))
        if (clampedProgress <= 0) {
            return movementAnimation.origin
        }
        if (clampedProgress >= path.length) {
            return path[path.length - 1]
        }

        const segmentIndex = Math.floor(clampedProgress)
        const fraction = clampedProgress - segmentIndex
        const start = segmentIndex === 0 ? movementAnimation.origin : path[segmentIndex - 1]
        const end = path[segmentIndex]
        return {
            "x": start.x + (end.x - start.x) * fraction,
            "y": start.y + (end.y - start.y) * fraction
        }
    }

    function movementGhostLeft() {
        const position = movementGhostPosition()
        if (!position) {
            return 0
        }
        return boardTileTopLeft(position).x + 4
    }

    function movementGhostTop() {
        const position = movementGhostPosition()
        if (!position) {
            return 0
        }
        return boardTileTopLeft(position).y + 4
    }

    function movementGhostColor() {
        if (movementAnimation && movementAnimation.owner_id === 2) {
            return "#8b1e3f"
        }
        return "#17324d"
    }

    function movementSummary() {
        if (!movementAnimation || !movementAnimation.active || !movementAnimation.path || movementAnimation.path.length === 0) {
            return ""
        }

        const origin = movementAnimation.origin
        const destination = movementAnimation.path[movementAnimation.path.length - 1]
        const unitName = movementAnimation.unit_type ? movementAnimation.unit_type : "unit"
        if (origin && destination) {
            return unitName + " #" + movementAnimation.unit_id + " moving from "
                   + origin.x + ", " + origin.y + " to "
                   + destination.x + ", " + destination.y + "."
        }
        return unitName + " #" + movementAnimation.unit_id + " moving."
    }

    function isMovementAnimationUnit(unit) {
        return !!unit
               && movementAnimation
               && movementAnimation.active
               && movementAnimation.unit_id === unit.id
    }

    function findMapUnit(x, y) {
        for (let i = 0; i < gameState.units.length; i++) {
            const unit = gameState.units[i]
            if (unit.embarked_in !== undefined && unit.embarked_in !== null) {
                continue
            }
            if (unit.position.x === x && unit.position.y === y) {
                return unit
            }
        }
        return null
    }

    function findTile(x, y) {
        for (let i = 0; i < gameState.tiles.length; i++) {
            const tile = gameState.tiles[i]
            if (tile.position.x === x && tile.position.y === y) {
                return tile
            }
        }
        return null
    }

    function findLegalTarget(x, y) {
        for (let i = 0; i < gameState.legal_targets.length; i++) {
            const target = gameState.legal_targets[i]
            if (target.position.x === x && target.position.y === y) {
                return target
            }
        }
        return null
    }

    function isPreviewFullStep(x, y) {
        if (!gameState.preview_full_path) {
            return false
        }
        for (let i = 0; i < gameState.preview_full_path.length; i++) {
            const step = gameState.preview_full_path[i]
            if (step.x === x && step.y === y) {
                return true
            }
        }
        return false
    }

    function isPreviewReachableStep(x, y) {
        if (!gameState.preview_reachable_path) {
            return false
        }
        for (let i = 0; i < gameState.preview_reachable_path.length; i++) {
            const step = gameState.preview_reachable_path[i]
            if (step.x === x && step.y === y) {
                return true
            }
        }
        return false
    }

    function isPreviewTarget(x, y) {
        return !!gameState.preview_target
               && gameState.preview_target.x === x
               && gameState.preview_target.y === y
    }

    function isPendingMoveTarget(x, y) {
        return !!gameState.pending_move_target
               && gameState.pending_move_target.x === x
               && gameState.pending_move_target.y === y
    }

    function isQueuedOrderTarget(x, y) {
        if (selectedUnitId < 0 || gameState.pending_move_target || gameState.preview_target) {
            return false
        }
        const unit = findUnitById(selectedUnitId)
        return !!(unit
                  && unit.queued_destination
                  && unit.queued_destination.x === x
                  && unit.queued_destination.y === y)
    }

    function isPreviewStop(x, y) {
        return !!gameState.preview_stop_position
               && gameState.preview_stop_position.x === x
               && gameState.preview_stop_position.y === y
    }

    function terrainColor(terrain) {
        return terrainFallbackColor(terrain)
    }

    function activeTheme() {
        if (themeLibrary[activeThemeId]) {
            return themeLibrary[activeThemeId]
        }
        return themeLibrary.empireDeluxe
    }

    function terrainSource(terrain) {
        const theme = activeTheme()
        if (theme && theme.terrainSources && theme.terrainSources[terrain]) {
            return theme.terrainSources[terrain]
        }
        return theme && theme.terrainSources && theme.terrainSources.plains ? theme.terrainSources.plains : ""
    }

    function terrainSourceForTile(tile, x, y) {
        if (!tile) {
            return terrainSource("plains")
        }
        if (!themeUsesTerrainImages()) {
            return ""
        }
        return terrainSource(tile.terrain)
    }

    function themeUsesTerrainImages() {
        const theme = activeTheme()
        return !!(theme && theme.useTerrainImages)
    }

    function isCoastalWaterTile(x, y) {
        const tile = findTile(x, y)
        if (!tile || tile.terrain !== "water") {
            return false
        }
        const neighbors = [
            findTile(x + 1, y),
            findTile(x - 1, y),
            findTile(x, y + 1),
            findTile(x, y - 1)
        ]
        for (let i = 0; i < neighbors.length; i++) {
            const neighbor = neighbors[i]
            if (neighbor && neighbor.terrain !== "water") {
                return true
            }
        }
        return false
    }

    function terrainFallbackColor(terrain) {
        const theme = activeTheme()
        if (theme && theme.terrainFallbackColors && theme.terrainFallbackColors[terrain]) {
            return theme.terrainFallbackColors[terrain]
        }
        return "#d9c7a4"
    }

    function unitIconSource(unitType) {
        return "../assets/icons/" + unitType + ".svg"
    }

    function cityIconSource() {
        return "../assets/icons/city.svg"
    }

    function hasCityIcon(tile) {
        return tile && tile.terrain === "city"
    }

    function ownerBadgeText(occupant, tile) {
        if (occupant) {
            return "" + occupant.owner_id
        }
        if (tile && tile.terrain === "city" && tile.city_owner_id !== null && tile.city_owner_id !== undefined) {
            return "" + tile.city_owner_id
        }
        return ""
    }

    function ownerBadgeColor(ownerId) {
        if (ownerId === 2) {
            return "#8b1e3f"
        }
        return "#17324d"
    }

    function cargoLabel(cargoUnitIds) {
        if (!cargoUnitIds || cargoUnitIds.length === 0) {
            return ""
        }
        return " [" + cargoUnitIds.join(", ") + "]"
    }

    function legalTargetColor(actionType) {
        if (actionType === "attack") {
            return "#c84c4c"
        }
        if (actionType === "embark") {
            return "#8167d8"
        }
        if (actionType === "disembark") {
            return "#2e9d8f"
        }
        return "#e8cf54"
    }

    function selectedTargetSummary() {
        if (!gameState.legal_targets || gameState.legal_targets.length === 0) {
            return "No legal adjacent actions"
        }
        const labels = []
        for (let i = 0; i < gameState.legal_targets.length; i++) {
            labels.push(gameState.legal_targets[i].label)
        }
        return labels.join(" | ")
    }

    function previewSummary() {
        if (!gameState.preview_target || !gameState.preview_full_path || gameState.preview_full_path.length === 0) {
            if (gameState.pending_move_target) {
                return "Pending: click the highlighted target again to confirm movement, or clear it."
            }
            if (selectedUnitHasOrders()) {
                const unit = findUnitById(selectedUnitId)
                return "Orders: this unit will continue toward "
                       + unit.queued_destination.x + ", " + unit.queued_destination.y
                       + " at the start of its next own turn"
            }
            return ""
        }
        if (gameState.preview_reaches_target) {
            return "Preview: reaches target this turn"
        }
        if (gameState.preview_stop_position) {
            return "Preview: stops this turn at "
                   + gameState.preview_stop_position.x + ", " + gameState.preview_stop_position.y
        }
        return "Preview: target not reachable from current position"
    }

    function selectedUnitHasOrders() {
        if (selectedUnitId < 0) {
            return false
        }
        const unit = findUnitById(selectedUnitId)
        return !!(unit && unit.queued_destination)
    }

    function selectedUnitHeadline() {
        if (selectedUnitId < 0) {
            return "No unit selected"
        }
        const unit = findUnitById(selectedUnitId)
        if (!unit) {
            return "Selected unit unavailable"
        }
        let text = "Selected: " + unit.unit_type + " #" + unit.id
        if (unit.attack_range !== undefined) {
            text += " | Range " + unit.attack_range
        }
        if (unit.queued_destination) {
            text += " | Orders " + unit.queued_destination.x + ", " + unit.queued_destination.y
        } else if (gameState.pending_move_target) {
            text += " | Pending " + gameState.pending_move_target.x + ", " + gameState.pending_move_target.y
        }
        return text
    }

    function themeOptions() {
        return [
            { "id": "classicFlat", "name": "Classic Flat" },
            { "id": "empireDeluxe", "name": "Empire Deluxe" }
        ]
    }

    function themeIndexForId(themeId) {
        const options = themeOptions()
        for (let i = 0; i < options.length; i++) {
            if (options[i].id === themeId) {
                return i
            }
        }
        return 0
    }

    function selectedThemeDescription() {
        const options = themeOptions()
        for (let i = 0; i < options.length; i++) {
            if (options[i].id === activeThemeId) {
                return options[i].name
            }
        }
        return "Classic Flat"
    }

    function findUnitById(unitId) {
        for (let i = 0; i < gameState.units.length; i++) {
            const unit = gameState.units[i]
            if (unit.id === unitId) {
                return unit
            }
        }
        return null
    }

    function ownedCities() {
        const cities = []
        for (let i = 0; i < gameState.tiles.length; i++) {
            const tile = gameState.tiles[i]
            if (tile.terrain === "city" && tile.city_owner_id === gameState.turn.current_player && tile.visible) {
                cities.push(tile)
            }
        }
        return cities
    }

    function cityBuildIndex(buildChoice, options) {
        const value = buildChoice || "infantry"
        for (let i = 0; i < options.length; i++) {
            if (options[i] === value) {
                return i
            }
        }
        return 0
    }

    function scenarioIndexForId(scenarioId) {
        const scenarios = (typeof gameController !== "undefined" && gameController) ? gameController.scenarios : []
        for (let i = 0; i < scenarios.length; i++) {
            if (scenarios[i].id === scenarioId) {
                return i
            }
        }
        return 0
    }

    function selectedScenarioDescription() {
        const scenarios = (typeof gameController !== "undefined" && gameController) ? gameController.scenarios : []
        for (let i = 0; i < scenarios.length; i++) {
            const scenario = scenarios[i]
            if (scenario.id === selectedScenarioId) {
                return scenario.description + " (" + scenario.width + "x" + scenario.height + ")"
            }
        }
        return ""
    }

    function roleLabel(cityRole) {
        if (cityRole === "capital") {
            return "Capital"
        }
        if (cityRole === "harbor") {
            return "Harbor"
        }
        if (cityRole === "factory") {
            return "Factory"
        }
        return "City"
    }

    function targetBadgeText(x, y) {
        if (isPendingMoveTarget(x, y)) {
            return "CONFIRM"
        }
        if (isQueuedOrderTarget(x, y)) {
            return "ORDERS"
        }
        if (isPreviewStop(x, y) && !gameState.preview_reaches_target) {
            return "STOP"
        }
        return ""
    }

    function targetBadgeColor(x, y) {
        if (isPendingMoveTarget(x, y)) {
            return "#17324d"
        }
        if (isQueuedOrderTarget(x, y)) {
            return "#317196"
        }
        return "#9b4b2f"
    }

    function describeTile(x, y, tile, occupant, legalTarget) {
        if (!tile) {
            return ""
        }
        let text = "Tile " + x + ", " + y + " | " + tile.terrain
        if (tile.terrain === "city") {
            text += tile.city_owner_id
                    ? " | " + roleLabel(tile.city_role) + " P" + tile.city_owner_id
                    : " | " + roleLabel(tile.city_role)
        }
        if (occupant) {
            text += " | " + occupant.unit_type + " #" + occupant.id + " P" + occupant.owner_id
        }
        if (legalTarget) {
            text += " | " + legalTarget.label
        }
        return text
    }
}
