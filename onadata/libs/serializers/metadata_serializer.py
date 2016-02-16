from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import ugettext as _
from rest_framework import serializers

from onadata.apps.logger.models import XForm
from onadata.apps.main.models import MetaData

CSV_CONTENT_TYPE = 'text/csv'
MEDIA_TYPE = 'media'
METADATA_TYPES = (
    ('data_license', _(u"Data License")),
    ('enketo_preview_url', _(u"Enketo Preview URL")),
    ('enketo_url', _(u"Enketo URL")),
    ('form_license', _(u"Form License")),
    ('mapbox_layer', _(u"Mapbox Layer")),
    (MEDIA_TYPE, _(u"Media")),
    ('public_link', _(u"Public Link")),
    ('source', _(u"Source")),
    ('supporting_doc', _(u"Supporting Document")),
    ('external_export', _(u"External Export")),
    ('textit', _(u"External Export"))
)


class XFormObjectRelatedField(serializers.RelatedField):
    """A custom field to represent the content_object generic relationship"""

    def to_internal_value(self, data):
        return XForm.objects.get(id=data)

    def to_representation(self, obj):
        """Serialize xform object"""
        if obj:
            content_object = obj.content_object

            if isinstance(content_object, XForm):
                return content_object

        raise Exception("Unexpected type of MetaData XForm")


class MetaDataSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    xform = XFormObjectRelatedField(queryset=XForm.objects.all())
    data_value = serializers.CharField(max_length=255,
                                       required=True)
    data_type = serializers.ChoiceField(choices=METADATA_TYPES)
    data_file = serializers.FileField(required=False)
    data_file_type = serializers.CharField(max_length=255, required=False,
                                           allow_blank=True)
    media_url = serializers.SerializerMethodField()
    date_created = serializers.ReadOnlyField()

    class Meta:
        model = MetaData
        fields = ('id', 'xform', 'data_value', 'data_type',
                  'data_file', 'data_file_type', 'media_url', 'file_hash',
                  'url', 'date_created')

    def get_media_url(self, obj):
        if obj.data_type == MEDIA_TYPE and getattr(obj, "data_file") \
                and getattr(obj.data_file, "url"):
            return obj.data_file.url

        return None

    def validate(self, attrs):
        """
        Validate url if we are adding a media uri instead of a media file
        """
        value = attrs.get('data_value')
        media = attrs.get('data_type')
        data_file = attrs.get('data_file')

        if media == 'media' and data_file is None:
            try:
                URLValidator()(value)
            except ValidationError:
                raise serializers.ValidationError({
                    'data_value': _(u"Invalid url %s." % value)
                })

        return attrs

    def create(self, validated_data):
        data_type = validated_data.get('data_type')
        data_file = validated_data.get('data_file')
        xform = validated_data.get('xform')
        data_value = data_file.name \
            if data_file else validated_data.get('data_value')
        data_file_type = data_file.content_type if data_file else None

        # not exactly sure what changed in the requests.FILES for django 1.7
        # csv files uploaded in windows do not have the text/csv content_type
        # this works around that
        if data_type == MEDIA_TYPE and data_file \
                and data_file.name.lower().endswith('.csv') \
                and data_file_type != CSV_CONTENT_TYPE:
            data_file_type = CSV_CONTENT_TYPE

        content_type = ContentType.objects.get_for_model(xform)

        return MetaData.objects.create(
            content_type=content_type,
            data_type=data_type,
            data_value=data_value,
            data_file=data_file,
            data_file_type=data_file_type,
            object_id=xform.id
        )
