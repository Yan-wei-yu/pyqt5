#include <vtkSmartPointer.h>
#include <vtkPLYReader.h>
#include <vtkAppendPolyData.h>
#include <vtkCleanPolyData.h>
#include <vtkActor.h>
#include <vtkPolyDataMapper.h>
#include <vtkRenderer.h>
#include <vtkRenderWindow.h>
#include <vtkRenderWindowInteractor.h>
#include <vtkPLYWriter.h>
#include <vtkTransformPolyDataFilter.h>
#include <vtkWindowToImageFilter.h>
#include <vtkImageResize.h>
#include <vtkImageShiftScale.h>
#include <vtkPNGWriter.h>
#include <vtkIntersectionPolyDataFilter.h>
#include <vtkCamera.h>
#include <vtkAutoInit.h>
#include <vtkInteractorStyleTrackballCamera.h>
#include <vtkProperty.h>
#include <vtkIterativeClosestPointTransform.h>
#include <vtkLandmarkTransform.h>
#include <vtkTransform.h>
#include <vtkCenterOfMass.h>
#include <vtkBooleanOperationPolyDataFilter.h>
#include <experimental/filesystem>

// ��l�� VTK �Ҳ�
VTK_MODULE_INIT(vtkRenderingOpenGL2);
VTK_MODULE_INIT(vtkInteractionStyle);

// �R�W�Ŷ��O�W
namespace fs = std::experimental::filesystem;

int main() {
	// �ץX�ʳ��M��r�����`�׹ϡA�T�O�r�X��m���T
	//std::vector<std::string> folderNames = { "Four-Surface", "Onlay", "Single-Surface", "Three-Surface", "Two-Surface" };
	std::vector<std::string> folderNames = { "Three-Surface" };

	// �]�w�ʳ��M��r�������|

	// �]�w��X�`�׹Ϫ���Ƨ����|
	std::string outputDirectory = "D://Users//user//Desktop//weiyundontdelete//GANdata//trainingdepth//depth90//";
	std::string outputtype = "Down";

	// �Ы�vtkAppendPolyData�MvtkCleanPolyData�L�o��
	vtkSmartPointer<vtkAppendPolyData> appendFilter1 = vtkSmartPointer<vtkAppendPolyData>::New();
	vtkSmartPointer<vtkAppendPolyData> appendFilter2 = vtkSmartPointer<vtkAppendPolyData>::New();
	vtkSmartPointer<vtkAppendPolyData> appendFilter3 = vtkSmartPointer<vtkAppendPolyData>::New();
	vtkSmartPointer<vtkCleanPolyData> cleanFilter1 = vtkSmartPointer<vtkCleanPolyData>::New();
	vtkSmartPointer<vtkCleanPolyData> cleanFilter2 = vtkSmartPointer<vtkCleanPolyData>::New();
	vtkSmartPointer<vtkCleanPolyData> cleanFilter3 = vtkSmartPointer<vtkCleanPolyData>::New();
	for (const std::string& folderName : folderNames) {
		// �]�w�ʳ��M��r�������|
		std::string path1 = "D://Users//user//Desktop//weiyundontdelete//GANdata//training//" + folderName + "//"+outputtype+"//";
		std::string path2 = "D://Users//user//Desktop//weiyundontdelete//GANdata//training//" + folderName + "//Up//";
		// ���N�B�z�ʳ��M��r�������
		for (const auto &entry1 : fs::directory_iterator(path1)) {
			if (fs::is_regular_file(entry1)) {
				std::string fileName1 = entry1.path().filename().string();
				// �b��r������󤤬d��ۦP�����
				for (const auto &entry2 : fs::directory_iterator(path2)) {
					if (fs::is_regular_file(entry2)) {
						std::string fileName2 = entry2.path().filename().string();
						// �p�G���ۦP�����
						if (fileName1 == fileName2) {
							// �M�ŹL�o�����s���A�ǳƲK�[�s���ҫ�
							cleanFilter1->RemoveAllInputConnections(0);
							cleanFilter2->RemoveAllInputConnections(0);
							cleanFilter3->RemoveAllInputConnections(0);
							appendFilter1->RemoveAllInputConnections(0);
							appendFilter2->RemoveAllInputConnections(0);
							appendFilter3->RemoveAllInputConnections(0);

							// Ū���ʳ��ҫ�
							vtkSmartPointer<vtkPLYReader> reader = vtkSmartPointer<vtkPLYReader>::New();
							reader->SetFileName((path1 + fileName1).c_str());
							reader->Update();

							// Ū����r���ҫ�
							vtkSmartPointer<vtkPLYReader> reader1 = vtkSmartPointer<vtkPLYReader>::New();
							reader1->SetFileName((path2 + fileName2).c_str());
							reader1->Update();

							// ����ʳ��ҫ����ߦ�m
							vtkSmartPointer<vtkCenterOfMass> centerOfMassFilter1 = vtkSmartPointer<vtkCenterOfMass>::New();
							centerOfMassFilter1->SetInputData(reader->GetOutput());
							centerOfMassFilter1->Update();
							double positiondown[3];
							centerOfMassFilter1->GetCenter(positiondown);

							// �����r���ҫ����ߦ�m
							vtkSmartPointer<vtkCenterOfMass> centerOfMassFilter2 = vtkSmartPointer<vtkCenterOfMass>::New();
							centerOfMassFilter2->SetInputData(reader1->GetOutput());
							centerOfMassFilter2->Update();
							double positionup[3];
							centerOfMassFilter2->GetCenter(positionup);
							//���w��0,0,0�A�ñ���Y-90�A���ᥭ����U�ƭ�l��m
							vtkSmartPointer<vtkTransform> transform = vtkSmartPointer<vtkTransform>::New();
							transform->Translate(-positiondown[0], -positiondown[1], -positiondown[2]);
							transform->RotateY(90);
							transform->Translate(positiondown[0], positiondown[1], positiondown[2]);

							vtkSmartPointer<vtkTransformPolyDataFilter> transformFilter = vtkSmartPointer<vtkTransformPolyDataFilter>::New();
							transformFilter->SetInputData(reader->GetOutput());
							transformFilter->SetTransform(transform);
							transformFilter->Update();


							//appendFilter1->AddInputConnection(reader->GetOutputPort());
							cleanFilter1->SetInputConnection(transformFilter->GetOutputPort());
							cleanFilter1->Update();

							appendFilter2->AddInputConnection(reader1->GetOutputPort());
							cleanFilter2->SetInputConnection(appendFilter2->GetOutputPort());
							cleanFilter2->Update();
							//// �X�֨��vtkPolyData
							appendFilter3->AddInputConnection(reader->GetOutputPort());
							appendFilter3->AddInputConnection(reader1->GetOutputPort());
							cleanFilter3->SetInputConnection(appendFilter3->GetOutputPort());
							cleanFilter3->Update();


							// �إ�PolyDataMapper
							vtkSmartPointer<vtkPolyDataMapper> mapper1 = vtkSmartPointer<vtkPolyDataMapper>::New();
							mapper1->SetInputConnection(cleanFilter1->GetOutputPort());

							vtkSmartPointer<vtkPolyDataMapper> mapper2 = vtkSmartPointer<vtkPolyDataMapper>::New();
							mapper2->SetInputConnection(cleanFilter2->GetOutputPort());

							// �إ�Actor
							vtkSmartPointer<vtkActor> actor = vtkSmartPointer<vtkActor>::New();
							actor->SetMapper(mapper1);

							vtkSmartPointer<vtkActor> actor1 = vtkSmartPointer<vtkActor>::New();
							actor1->SetMapper(mapper2);
							actor1->GetProperty()->SetOpacity(0);



							vtkSmartPointer<vtkRenderer> renderer = vtkSmartPointer<vtkRenderer>::New();
							vtkSmartPointer<vtkRenderWindow> renderWindow = vtkSmartPointer<vtkRenderWindow>::New();

							// �N�ҫ���Actor�K�[���V��
							renderer->AddActor(actor);
							/*	renderer->AddActor(actor1);*/
								//�o��]�m����256*256�I���¦�
							renderWindow->SetSize(256, 256);
							renderer->SetBackground(0, 0, 0);
							renderer->ResetCamera();
							renderWindow->AddRenderer(renderer);
							vtkSmartPointer<vtkRenderWindowInteractor> renderWindowInteractor = vtkSmartPointer<vtkRenderWindowInteractor>::New();
							renderWindowInteractor->SetRenderWindow(renderWindow);


							//�Ы�polydata�ΨӦsBoundingbox��ơAGetbound�|�NX�BY�BZ�̤p�P�̤j���O���C
							vtkSmartPointer<vtkPolyData> polyData = vtkSmartPointer<vtkPolyData>::New();
							polyData = cleanFilter1->GetOutput();
							double bounds[6];
							polyData->GetBounds(bounds);
							double minX = bounds[0];
							double maxX = bounds[1];
							double minY = bounds[2];
							double maxY = bounds[3];
							double minZ = bounds[4];
							double maxZ = bounds[5];
							double center1[3] = { (bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2, (bounds[4] + bounds[5]) / 2 };
							if (fileName1 == "data0004.ply") {
								printf("123");
							}
							// �Ұʴ�V���f
							vtkSmartPointer<vtkInteractorStyleTrackballCamera> style = vtkSmartPointer<vtkInteractorStyleTrackballCamera>::New();
							renderWindowInteractor->SetInteractorStyle(style);
							renderWindow->Render();


							vtkCamera* cam1 = vtkCamera::New();
							cam1 = renderer->GetActiveCamera();

							//�񻷵�����ƭȬ���
							double clip[2] = { 0 };
							cam1->GetClippingRange(clip);
							cam1->SetFocalPoint(center1);
							cam1->SetParallelProjection(true); // �ҥΥ����v�Ҧ�

							//�o�䬰�F�p��Bounding �̪�Y�ȡA���F���̾A�X�����ť���
							double boundinglongscale = maxY - minY;;
							double boundinglongdepth = (maxX - minX);
							cam1->SetParallelScale((boundinglongscale)/2 + 0.1); // �o�̪�boundinglong�O�ҫ�Y�b�W���̤j���Z�ASetParallelScale��k�O�Ψӳ]�m�����v�����f�ث�

							////�o�䬰�F��o�۾���J�I���Z��
							double clp_dis = clip[1] - clip[0]; // 	//�o�̬O��X��v���������Z���]clp_dis�^
							cam1->SetClippingRange(clip[0], clip[1]-clp_dis*0.5);
							renderer->SetActiveCamera(cam1);

							// �Ы�vtkWindowToImageFilter�H�����V���f�`�׹�
							vtkSmartPointer<vtkWindowToImageFilter> depthImageFilter = vtkSmartPointer<vtkWindowToImageFilter>::New();
							depthImageFilter->SetInput(renderWindow);
							depthImageFilter->SetInputBufferTypeToZBuffer();

							// �Ы�vtkImageShiftScale�H�N�`�׭ȬM�g��0-255���d��
							vtkSmartPointer<vtkImageShiftScale> scaleFilter = vtkSmartPointer<vtkImageShiftScale>::New();
							scaleFilter->SetInputConnection(depthImageFilter->GetOutputPort());
							scaleFilter->SetOutputScalarTypeToUnsignedChar();
							scaleFilter->SetShift(-1);
							scaleFilter->SetScale(-255);

							// �]�m��X�`�׹Ϫ������|
							std::string outputFilePath = outputDirectory  + fileName1.substr(0, fileName1.find(".")) + ".png";

							// �Ы�vtkPNGWriter�H�O�s�`�׹Ϲ�
							vtkSmartPointer<vtkPNGWriter> depthImageWriter = vtkSmartPointer<vtkPNGWriter>::New();
							depthImageWriter->SetFileName(outputFilePath.c_str());
							depthImageWriter->SetInputConnection(scaleFilter->GetOutputPort());
							depthImageWriter->Write();
						}
					}
				}
			}
		}


	}
	return 0;
}
