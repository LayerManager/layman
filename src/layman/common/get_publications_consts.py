BBOX_PATTERN = r"^(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$"
INTEGER_PATTERN = f"^([-+]?[0-9]+)$"
CRS_PATTERN = r"^(\w+:\d+)$"

FILTER_FULL_TEXT = 'full_text_filter'
FILTER_BBOX = 'bbox_filter'
FILTER_BBOX_CRS = 'bbox_filter_crs'

ORDER_BY_PARAM = 'order_by'
ORDER_BY_FULL_TEXT = 'full_text'
ORDER_BY_TITLE = 'title'
ORDER_BY_LAST_CHANGE = 'last_change'
ORDER_BY_BBOX = 'bbox'
ORDERING_BBOX = 'ordering_bbox'

LIMIT = 'limit'
OFFSET = 'offset'
