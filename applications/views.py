from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Application
from .serializers import ApplicationSerializer
from .permissions import IsPropertyLandlord


class ApplicationCreateView(generics.CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user)


class MyApplicationsView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(tenant=self.request.user).select_related('property')


class ApplicationDecisionView(APIView):
    permission_classes = [IsAuthenticated, IsPropertyLandlord]

    ALLOWED_TRANSITIONS = {
        Application.Status.PENDING: [Application.Status.APPROVED, Application.Status.REJECTED],
    }

    def post(self, request, pk):
        application = generics.get_object_or_404(Application, pk=pk)
        self.check_object_permissions(request, application)

        new_status = request.data.get('status')
        if new_status not in [Application.Status.APPROVED, Application.Status.REJECTED]:
            return Response(
                {"detail": "status must be APPROVED or REJECTED."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_next = self.ALLOWED_TRANSITIONS.get(application.status, [])
        if new_status not in allowed_next:
            return Response(
                {"detail": f"Cannot transition from {application.status} to {new_status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application.status = new_status
        application.save()
        return Response(ApplicationSerializer(application).data)