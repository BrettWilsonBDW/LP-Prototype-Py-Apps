import sympy as sp

import re

import sys
import pygame
import OpenGL.GL as gl
from imgui.integrations.pygame import PygameRenderer
import imgui
import os
import copy

import dualSimplex
import mathPrelims


def testInput():
    isMin = False

    objFunc = [60, 30, 20]
    constraints = [[8, 6, 1, 48, 0],
                   [4, 2, 1.5, 20, 0],
                   [2, 1.5, 0.5, 8, 0],
                   ]
    
    AddedConstraints = [
        [0, 0, 1, 0, 5, 0],
    ]

    objFunc = [30, 28, 26, 30]
    constraints = [[8, 8, 4, 4, 160, 0],
                   [1, 0, 0, 0, 5, 0],
                   [1, 0, 0, 0, 5, 1],
                   [1, 1, 1, 1, 20, 1],
                   ]


    AddedConstraints = [
        [1, -1, 0, 0, 0, 0],
        [-1, 1, 0, 0, 0, 1],
    ]

    return objFunc, constraints, isMin, AddedConstraints


def GetMathPrelims(objFunc, constraints, isMin, absRule=False):
    changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = mathPrelims.doSensitivityAnalysis(
        objFunc, constraints, isMin, absRule)
    return changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots


def DoAddActivity(objFunc, constraints, isMin, activity, absRule=False):
    # changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = mathPrelims.doSensitivityAnalysis(objFunc, constraints, isMin, absRule)
    changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = GetMathPrelims(
        objFunc, constraints, isMin, absRule)
    
    matrixAct = sp.Matrix(activity[1:])

    c = matrixAct.transpose() * matrixCbvNegOne

    cTop = c[0, 0] - activity[0]

    b = matrixAct.transpose() * matrixBNegOne

    tdisplayCol = b.tolist()

    displayCol = []
    for i in range(len(tdisplayCol[-1])):
        displayCol.append(tdisplayCol[-1][i])

    displayCol.insert(0, cTop)

    print(displayCol)

    return displayCol


def DoAddConstraint(objFunc, constraints, isMin, AddedConstraints, absRule=False):
    changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = GetMathPrelims(
        objFunc, constraints, isMin=False, absRule=False)

    newTab = copy.deepcopy(changingTable)

    for k in range(len(AddedConstraints)):
        for i in range(len(changingTable)):
            newTab[i].insert(-1, 0.0)

        newCon = []
        for i in range(len(changingTable[0]) + len(AddedConstraints)):
            newCon.append(0.0)

        for i in range(len(AddedConstraints[k]) - 2):
            newCon[i] = float(AddedConstraints[k][i])

        newCon[-1] = float(AddedConstraints[k][-2])

        slackSpot = ((len(newCon) - len(AddedConstraints)) - 1) + k
        if AddedConstraints[k][-1] == 1:
            newCon[slackSpot] = -1.0
        else:
            newCon[slackSpot] = 1.0

        newTab.append(newCon)

    print("\nunfixed tab")
    for i in range(len(newTab)):
        for j in range(len(newTab[i])):
            print(newTab[i][j], end="     ")
        print()
    print("\n\n")


    displayTab = copy.deepcopy(newTab)
    for k in range(len(AddedConstraints)):
        for i in range(len(newTab[0])):
            tLst = []
            for j in range(len(newTab)):
                tLst.append(newTab[j][i])
            if i in basicVarSpots:
                if tLst[-k-1] != 0:
                    bottomRow = ((k) + len(newTab) - len(AddedConstraints))
                    for spotsCtr in range(len(newTab) - len(AddedConstraints)):
                        if tLst[spotsCtr] == 1:
                            topRow = spotsCtr
                            tempNewRow = []
                            for newTabCrt in range(len(newTab[0])):
                                if newTab[bottomRow][i] == -1:
                                    tempNewRow.append(
                                        newTab[bottomRow][newTabCrt] + newTab[topRow][newTabCrt])
                                elif newTab[bottomRow][i] == 1:
                                    tempNewRow.append(
                                        newTab[bottomRow][newTabCrt] - newTab[topRow][newTabCrt])
                                else:
                                    print("do it by hand")

                            displayTab[bottomRow] = tempNewRow

    print("fixed tab")
    for i in range(len(displayTab)):
        for j in range(len(displayTab[i])):
            print(displayTab[i][j], end="     ")
        print()

def DoGui():
    pygame.init()
    size = 1920 / 2, 1080 / 2

    os.system('cls' if os.name == 'nt' else 'clear')
    # print("\nBrett's simplex prototype tool for dual simplex problems\n")

    pygame.display.set_mode(size, pygame.DOUBLEBUF |
                            pygame.OPENGL | pygame.RESIZABLE)

    pygame.display.set_caption("dual Simplex Prototype")

    icon = pygame.Surface((1, 1)).convert_alpha()
    icon.fill((0, 0, 0, 1))
    pygame.display.set_icon(icon)

    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size

    # simplex specific vars

    problemType = "Max"
    absProblemType = "abs Off"

    # dual constraints
    amtOfObjVars = 2
    objFunc = [0.0, 0.0]

    constraints = [[0.0, 0.0, 0.0, 0.0]]
    signItems = ["<=", ">="]
    signItemsChoices = [0]

    amtOfConstraints = 1

    activity = [0.0, 0.0]

    absRule = False

    problemChoice = "activity"

    problemState = True

    actDisplayCol = []

    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            impl.process_event(event)

        imgui.new_frame()

        window_size = pygame.display.get_window_size()

        imgui.set_next_window_position(0, 0)  # Set the window position
        imgui.set_next_window_size(
            (window_size[0]), (window_size[1]))  # Set the window size
        imgui.begin("Tableaus Output",
                    flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE)

        if imgui.radio_button("Max", problemType == "Max"):
            problemType = "Max"

        if imgui.radio_button("Min", problemType == "Min"):
            problemType = "Min"

        imgui.text("Problem is: {}".format(problemType))

        if imgui.radio_button("abs on", absProblemType == "abs On"):
            absProblemType = "abs On"

        if imgui.radio_button("abs off", absProblemType == "abs Off"):
            absProblemType = "abs Off"

        imgui.text("absolute rule is: {}".format(absProblemType))


        # obj vars ===========================================
        if imgui.button("decision variables +"):
            amtOfObjVars += 1
            for i in range(len(constraints)):
                constraints[i].append(0.0)
            objFunc.append(0.0)

        imgui.same_line()

        if imgui.button("decision variables -"):
            if amtOfObjVars != 2:
                amtOfObjVars += -1
                for i in range(len(constraints)):
                    constraints[i].pop()
                objFunc.pop()

        imgui.spacing()

        for i in range(len(objFunc)):
            # value = objFunc[i]
            value = float(objFunc[i])
            imgui.set_next_item_width(50)
            imgui.same_line()
            # changed, objFunc[i] = imgui.input_float(
            changed, objFunc[i] = imgui.input_float(
                "objFunc {}".format(i + 1), value)

            if changed:
                pass

        if imgui.button("Constraint +"):
            amtOfConstraints += 1
            constraints.append([0.0] * amtOfObjVars)
            constraints[-1].append(0.0)  # add sign spot
            constraints[-1].append(0.0)  # add rhs spot
            signItemsChoices.append(0)

            # activity[-1].append(0.0 * len(constraints))
            activity.append(0.0)

        imgui.same_line()

        if imgui.button("Constraint -"):
            if amtOfConstraints != 1:
                amtOfConstraints += -1
                constraints.pop()
                signItemsChoices.pop()

                activity.pop()

        # spaceGui(6)
        for i in range(amtOfConstraints):
            imgui.spacing()
            if len(constraints) <= i:
                # Fill with default values if needed
                constraints.append([0.0] * (amtOfObjVars + 2))

            for j in range(amtOfObjVars):
                # value = constraints[i][j]
                value = float(constraints[i][j])
                imgui.set_next_item_width(50)
                imgui.same_line()
                # changed, xValue = imgui.input_float(
                changed, xValue = imgui.input_float(
                    "xC{}{}".format(i, j), value)
                if changed:
                    constraints[i][j] = xValue

            imgui.same_line()
            imgui.push_item_width(50)
            changed, selectedItemSign = imgui.combo(
                "comboC{}{}".format(i, j), signItemsChoices[i], signItems)
            if changed:
                signItemsChoices[i] = selectedItemSign
                constraints[i][-1] = signItemsChoices[i]

            imgui.pop_item_width()
            imgui.same_line()
            imgui.set_next_item_width(50)
            # rhsValue = constraints[i][-2]
            rhsValue = float(constraints[i][-2])
            # rhsChanged, rhs = imgui.input_float(
            rhsChanged, rhs = imgui.input_float(
                "RHSC{}{}".format(i, j), rhsValue)

            if rhsChanged:
                constraints[i][-2] = rhs

        if imgui.radio_button("adding activity", problemChoice == "activity"):
            problemChoice = "activity"

        imgui.same_line(0, 20)

        if imgui.radio_button("adding constraints", problemChoice == "constraints"):
            problemChoice = "constraints"

        imgui.text("the current problem is adding {}".format(problemChoice))

        if problemType == "Min":
            isMin = True
        else:
            isMin = False

        if absProblemType == "abs On":
            absRule = True
        else:
            absRule = False

        if problemChoice == "activity":
            problemState = True
        else:
            problemState = False

        if problemState:
            imgui.new_line()
            # activity.append(0.0 * len(constraints))
            for i in range(len(constraints) + 1):
                value = float(activity[i])
                imgui.set_next_item_width(50)
                imgui.same_line()
                # changed, objFunc[i] = imgui.input_float(
                # for k in range(len(constraints)):
                #     activity.append(0.0)
                imgui.new_line()
                changed, activity[i] = imgui.input_float(
                    "activity {}".format(i + 1), value)

        if not problemState:
            pass

        imgui.spacing()
        imgui.spacing()
        if imgui.button("Solve"):
            try:
                objFunc, constraints, isMin, AddedConstraints = testInput()
                activity = [40.0, 5.0, 0.0, 0.0, 1.0]
                # print(objFunc)
                # print(constraints)
                print(activity)

                if problemState:
                    actDisplayCol = DoAddActivity(objFunc, constraints, isMin, activity, absRule)

            except Exception as e:
                print("math error:", e)

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        if problemState:
            for i in range(len(actDisplayCol)):
                if i == 0:
                    imgui.text("Activity    ")
                else:
                    imgui.text("Constraint {}".format(i))
                imgui.same_line()
                imgui.text("{:>15.3f}".format(float(actDisplayCol[i])))
                imgui.new_line()

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        imgui.end()

        # gl stuff
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()


def main():
    # GetMathPrelims(testInput()[0], testInput()[1], testInput()[2])
    # DoAddActivity(testInput()[0], testInput()[1], testInput()[2], True)

    # DoAddConstraint(testInput()[0], testInput()[1], testInput()[2])

    # DoAddActivity(testInput()[0], testInput()[1], testInput()[2], True)

    # DoAddConstraint(testInput()[0], testInput()[1], testInput()[
    #                 2], testInput()[3], absRule=False)

    DoGui()

main()