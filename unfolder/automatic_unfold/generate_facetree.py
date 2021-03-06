import maya.OpenMaya as om

from unfolder.util.helpers import setIter
from unfolder.tree.tree import Tree


def createFacetreeLightning(dagPath, connectedFaces):
    """ Create a face tree with depth first strategy
    """

    def createFaceIter(initialFace):
        retval = om.MItMeshPolygon(dagPath)
        setIter(retval, initialFace)
        return retval

    def extractConnectedFaces(faceIter, remainingFaces):
        face = faceIter.index()

        connectedFaces = om.MIntArray()
        faceIter.getConnectedFaces(connectedFaces)
        neighbours = frozenset(connectedFaces) & remainingFaces
        remainingFaces -= neighbours

        children = []
        for connectedFace in neighbours:
            setIter(faceIter, connectedFace)
            children.append(extractConnectedFaces(faceIter, remainingFaces))

        node = Tree(face)
        node.children = children
        return node

    print("duplicating model")
    initialFace = connectedFaces[0]
    remainingFaces = set(connectedFaces[1:])
    faceIter = createFaceIter(initialFace)
    tree = extractConnectedFaces(faceIter, remainingFaces)
    print("duplicating model ... done")
    return tree


def createFacetreeSpiral(dagPath, connectedFaces):
    """ Create a face tree with maximum children per parent node strategy
    """

    def createFaceIter(initialFace):
        faceIter = om.MItMeshPolygon(dagPath)
        setIter(faceIter, initialFace)
        return faceIter

    def traverseTreeStub(node, remainingFaces):
        if node.children:
            for child in node.children:
                traverseTreeStub(child, remainingFaces)
        else:
            addDirectChildren(node, remainingFaces)

    def addDirectChildren(node, remainingFaces):
        faceIter = createFaceIter(node.face)

        connectedFaces = om.MIntArray()
        faceIter.getConnectedFaces(connectedFaces)
        neighbours = frozenset(connectedFaces) & remainingFaces
        remainingFaces -= neighbours

        for connectedFace in neighbours:
            node.addChild(connectedFace)

    print("duplicating model")
    initialFace = connectedFaces[0]
    remainingFaces = set(connectedFaces[1:])
    tree = Tree(initialFace)
    while remainingFaces:
        traverseTreeStub(tree, remainingFaces)
    print("duplicating model ... done")
    return tree

def createFacetreeSelectionOrder(dagPath, orderedSelectedFaces):

    def createFaceIter(initialFace):
        faceIter = om.MItMeshPolygon(dagPath)
        setIter(faceIter, initialFace)
        return faceIter

    def addFaceStripToNode(node, remainingFaces):
            faceIter = createFaceIter(node.face)

            connectedFaces = om.MIntArray()
            faceIter.getConnectedFaces(connectedFaces)
            newFace = remainingFaces[0]
            if newFace in frozenset(connectedFaces):
                del remainingFaces[0]
                newNode = node.addChild(newFace)
                if remainingFaces:
                    addNextFaceStripToSubtree(newNode, remainingFaces)
                return True

    def addNextFaceStripToSubtree(node, remainingFaces):
        if addFaceStripToNode(node, remainingFaces):
            return True
        else:
            for child in node.children:
                if addNextFaceStripToSubtree(child, remainingFaces):
                    return True
        return False

    print("duplicating model")
    initialFace = orderedSelectedFaces[0]
    remainingFaces = orderedSelectedFaces[1:]
    tree = Tree(initialFace)
    while remainingFaces:
        addNextFaceStripToSubtree(tree, remainingFaces)
    print("duplicating model ... done")
    return tree