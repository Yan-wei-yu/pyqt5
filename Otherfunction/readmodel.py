import vtk
import os
import math

def load_3d_model(filename):
    _, extension = os.path.splitext(filename)
    extension = extension.lower()

    if extension == '.ply':
        reader = vtk.vtkPLYReader()
    elif extension == '.stl':
        reader = vtk.vtkSTLReader()
    elif extension == '.obj':
        reader = vtk.vtkOBJReader()
    else:
        raise ValueError(f"Unsupported file format: {extension}")

    reader.SetFileName(filename)
    reader.Update()
    return reader.GetOutput()

def create_actor(polydata, color):
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polydata)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)
    return actor

def calculate_center (actor):
    bounds = actor.GetBounds()
    center = [
        (bounds[1] + bounds[0]) *0.5,
        (bounds[3] + bounds[2]) *0.5,
        (bounds[5] + bounds[4]) *0.5
    ]
    return center

def twomodel_bound(upper_bounds,lower_bounds):
    combined_bounds = [
        min(upper_bounds[0], lower_bounds[0]),  # x_min
        max(upper_bounds[1], lower_bounds[1]),  # x_max
        min(upper_bounds[2], lower_bounds[2]),  # y_min
        max(upper_bounds[3], lower_bounds[3]),  # y_max
        min(upper_bounds[4], lower_bounds[4]),  # z_min
        max(upper_bounds[5], lower_bounds[5])   # z_max
    ]
    return combined_bounds

def rotate_actor(actor, center, angle):
    transform = vtk.vtkTransform()
    transform.Translate(-center[0], -center[1], -center[2])
    transform.RotateY(angle) 
    transform.RotateX(0) 
    transform.RotateZ(0) 

    transform.Translate(center[0], center[1], center[2])
    actor.SetUserTransform(transform)



def setup_camera(renderer, render_window, center1, center2, lower_bound, upper_opacity,angle):
    
    # Get the active camera from the renderer
    cam1 = renderer.GetActiveCamera()

    # Camera position and clip values initialization
    cam_position = [0.0, 0.0, 0.0]

    # Set focal point to center1
    cam1.SetFocalPoint(center1)

    # Enable parallel projection
    cam1.SetParallelProjection(True)

    # Get the camera position
    cam_position=cam1.GetPosition()

    # Calculate distances from camera to model centers
    distance_cam_to_bb = math.sqrt(
        (cam_position[0] - center1[0])**2 +
        (cam_position[1] - center1[1])**2 +
        (cam_position[2] - center1[2])**2
    )


    # Calculate near and far clipping planes
    near = distance_cam_to_bb - ((lower_bound[5] - lower_bound[4]) * 0.5)
    far = distance_cam_to_bb + ((lower_bound[5] - lower_bound[4]) * 0.5)

    # Set the parallel scale based on Y bounding box values
    cam1.SetParallelScale((lower_bound[3] - lower_bound[2]) * 0.5)

    # # Set the clipping range based on output data
    if upper_opacity != 0 and center2!=None :
        distance_cam_to_bb_up = math.sqrt(
            (cam_position[0] - center2[0])**2 +
            (cam_position[1] - center2[1])**2 +
            (cam_position[2] - center2[2])**2
        )
        gap_and_down = distance_cam_to_bb - distance_cam_to_bb_up

        cam1.SetClippingRange(near - gap_and_down, far)
    elif angle != 0:
        cam1.SetClippingRange(near, far-((far-near)*0.5))
    else:
        cam1.SetClippingRange(near, far)

    # # Set the active camera for the renderer
    renderer.SetActiveCamera(cam1)
    # Create vtkWindowToImageFilter to get the depth image from the render window
    depth_image_filter = vtk.vtkWindowToImageFilter()
    depth_image_filter.SetInput(render_window)
    depth_image_filter.SetInputBufferTypeToZBuffer()

    # Create vtkImageShiftScale to map depth values to the 0-255 range
    scale_filter = vtk.vtkImageShiftScale()
    scale_filter.SetInputConnection(depth_image_filter.GetOutputPort())
    scale_filter.SetOutputScalarTypeToUnsignedChar()
    scale_filter.SetShift(-1)
    scale_filter.SetScale(-255)

    return scale_filter


def save_depth_image(output_file_path, scale_filter):
    # Create a vtkPNGWriter to save the depth image
    depth_image_writer = vtk.vtkPNGWriter()

    # Set the output file path
    depth_image_writer.SetFileName(output_file_path)

    # Connect the writer to the scale filter output (which is assumed to be a valid filter with output)
    depth_image_writer.SetInputConnection(scale_filter.GetOutputPort())

    # Write the image to the specified file
    depth_image_writer.Write()

    # The pipeline is set, you can now execute the filters and work with the output image.


def render_file_in_second_window(render2, file_path):
    """
    Renders either an STL model or a PNG image in the second VTK render window.

    Args:
        render2 (vtkRenderer): The VTK renderer to render the file in.
        file_path (str): The file path of the image (PNG) or model (STL).
    """
    # Ensure the file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    # Get the file extension to determine whether it's PNG or STL
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".png":
        # Handle PNG files with vtkPNGReader
        reader = vtk.vtkPNGReader()
    elif file_extension == ".stl":
        # Handle STL files with vtkSTLReader
        reader = vtk.vtkSTLReader()
    else:
        print(f"Unsupported file format: {file_extension}")
        return
    reader.SetFileName(file_path)
    reader.Update()

    # Create an actor for rendering
    if file_extension == ".png":
        # For PNG, use vtkImageActor
        actor = vtk.vtkImageActor()
        actor.GetMapper().SetInputConnection(reader.GetOutputPort())
    elif file_extension == ".stl":
        # For STL, use vtkActor and vtkPolyDataMapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

    # Clear any previous rendering in vtk_renderer2
    render2.RemoveAllViewProps()

    # Add the actor to the renderer
    render2.AddActor(actor)

    # Reset the camera and render
    render2.ResetCamera()
    render2.GetRenderWindow().Render()