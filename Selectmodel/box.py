from vtkmodules.vtkInteractionStyle import vtkInteractorStyleRubberBand3D
import vtk
class BoxInteractor(vtkInteractorStyleRubberBand3D):
    def __init__(self,poly_data,renderer):
        super().__init__()
        self.renderer = renderer
        self.poly_data = poly_data
        self.selection_frustum = None
        self.extract_geometry = None
        self.selected_poly_data = None
        self.end_position = [0,0]
        self.start_position = [0,0]
        self.boxArea = vtk.vtkAreaPicker()
        self.colorActors = []
        self.RemoveObservers("LeftButtonPressEvent")
        self.RemoveObservers("LeftButtonUpEvent")
        self.RemoveObservers("RightButtonPressEvent")
        self.RemoveObservers("RightButtonReleaseEvent")
        self.RemoveObservers("MiddleButtonPressEvent")
        self.RemoveObservers("MiddleButtonReleaseEvent")
        self.RemoveObservers("MiddleButtonForwardEvent")
        self.RemoveObservers("MiddleButtonBackwardEvent")
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonPress)
        self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonUp)
        self.AddObserver("RightButtonPressEvent", self.onRightButtonPress)
        self.AddObserver("RightButtonReleaseEvent", self.onRightButtonUp)
        self.AddObserver("MiddleButtonPressEvent", self.onMiddleButtonDown)
        self.AddObserver("MiddleButtonReleaseEvent", self.onMiddleButtonUp)
        self.AddObserver("MiddleButtonForwardEvent", self.onMiddleButtonForward)
        self.AddObserver("MiddleButtonBackwardEvent", self.onMiddleButtonBackward)

    def onMiddleButtonDown(self,obj,event):
        return
    def onMiddleButtonUp(self,obj,event):
        return
    def onMiddleButtonForward(self,obj,event):
        return
    def onMiddleButtonBackward(self,obj,event):
        return
    def onRightButtonPress(self, obj, event):
        return
    def onRightButtonUp(self, obj, event):
        return
    def onLeftButtonPress(self, obj, event):
        start_coord = self.GetInteractor().GetEventPosition()
        self.start_position = [start_coord[0], start_coord[1]]
        super().OnLeftButtonDown()
        return
    def onLeftButtonUp(self, obj, event):
        end_coord = self.GetInteractor().GetEventPosition()
        self.end_position = [end_coord[0], end_coord[1]]
        super().OnLeftButtonUp()
        return
    def boxSelectArea(self):
        self.boxArea.AreaPick(self.start_position[0], self.start_position[1], self.end_position[0], self.end_position[1], self.renderer)
        self.selection_frustum = self.boxArea.GetFrustum()

        self.extract_geometry = vtk.vtkExtractGeometry()
        self.extract_geometry.SetInputData(self.poly_data)
        self.extract_geometry.SetImplicitFunction(self.selection_frustum)
        self.extract_geometry.Update()

        self.selected_poly_data = self.extract_geometry.GetOutput()

        self.geometry_filter = vtk.vtkGeometryFilter()
        self.geometry_filter.SetInputData(self.selected_poly_data)
        self.geometry_filter.Update()
        return self.geometry_filter.GetOutput()

        
    def show_all_area(self,input_model):
        mapper = vtk.vtkPolyDataMapper()
        actor = vtk.vtkActor()
        mapper.SetInputData(input_model)
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # 設定紅色

        self.colorActors.append(actor)
        self.renderer.AddActor(actor)
        self.GetInteractor().GetRenderWindow().Render()
    # 移除染色資料
    def unRenderAllSelectors(self):
        for colorActor in self.colorActors:
            self.renderer.RemoveActor(colorActor)
        self.GetInteractor().GetRenderWindow().Render()
    def interactorSetter(self,interactor): # 避免放在建構子直接初始化
        self.SetInteractor(interactor) # 設定互動器



