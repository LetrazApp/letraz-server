from rest_framework import serializers

class ResumeExportResponse(serializers.Serializer):
    pdf_url = serializers.UUIDField(help_text='The public CDN URL of the exported PDF file of the resume')
    latex_url = serializers.UUIDField(help_text='The public CDN URL of the exported TEX file of the resume')