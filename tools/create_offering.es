PUT /offerings_v2
{
  "mappings": {
    "properties": {
      "RSVP": {
        "type": "text"
      },
      "RSVPDeadline": {
        "type": "date"
      },
      "activity": {
        "type": "text",  // 改为 text 类型，支持文本搜索
        "copy_to": "activityEmbeddings"  // 将内容复制到 activity_embeddings 字段
      },
      "activityEmbeddings": {
        "type": "semantic_text",  // 新增字段，用于语义搜索
        "inference_id": "my-inference-endpoint",
        "model_settings": {
          "task_type": "text_embedding",
          "dimensions": 1536,
          "similarity": "dot_product",
          "element_type": "float"
        }
      },
      "activityCategory": {
        "type": "text",  // 改为 text 类型，支持文本搜索
        "copy_to": "activityCategoryEmbeddings"  // 将内容复制到 activity_embeddings 字段
      },
      "activityCategoryEmbeddings": {
        "type": "semantic_text",
        "inference_id": "my-inference-endpoint",
        "model_settings": {
          "task_type": "text_embedding",
          "dimensions": 1536,
          "similarity": "dot_product",
          "element_type": "float"
        }
      },
      "ageGroup": {
        "type": "integer_range"
      },
      "businessFullName": {
        "type": "text",  // 改为 text 类型，支持文本搜索
        "copy_to": "businessFullNameEmbeddings"  // 将内容复制到 activity_embeddings 字段
      },
      "businessFullNameEmbeddings": {
        "type": "semantic_text",
        "inference_id": "my-inference-endpoint",
        "model_settings": {
          "task_type": "text_embedding",
          "dimensions": 1536,
          "similarity": "dot_product",
          "element_type": "float"
        }
      },
      "campAmenities": {
        "type": "keyword"
      },
      "campSessionOptions": {
        "type": "keyword"
      },
      "facility": {
        "type": "keyword"
      },
      "hyperlink": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "location": {
        "properties": {
          "geo_info": {
            "type": "geo_point"
          },
          "name": {
            "type": "text"
          }
        }
      },
      "locationDisplayName": {
        "type": "keyword"
      },
      "locationType": {
        "type": "keyword"
      },
      "lunchIncluded": {
        "type": "keyword"
      },
      "name": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "offeringInsightSummary": {
        "type": "text",  // 改为 text 类型，支持文本搜索
        "copy_to": "offeringInsightSummaryEmbeddings"  // 将内容复制到 activity_embeddings 字段
      },
      "offeringInsightSummaryEmbeddings": {
        "type": "semantic_text",
        "inference_id": "my-inference-endpoint",
        "model_settings": {
          "task_type": "text_embedding",
          "dimensions": 1536,
          "similarity": "dot_product",
          "element_type": "float"
        }
      },
      "offeringName": {
        "type": "text",  // 改为 text 类型，支持文本搜索
        "copy_to": "offeringNameEmbeddings"  // 将内容复制到 activity_embeddings 字段
      },
      "offeringNameEmbeddings": {
        "type": "semantic_text",
        "inference_id": "my-inference-endpoint"
      },
      "offeringType": {
        "type": "keyword"
      },
      "pricing": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "schedule": {
        "properties": {
          "blackoutDate": {
            "type": "date"
          },
          "classDay": {
            "type": "keyword"
          },
          "durationSeason": {
            "type": "keyword"
          },
          "endDate": {
            "type": "date"
          },
          "frequency": {
            "type": "keyword"
          },
          "startDate": {
            "type": "date"
          },
          "time": {
            "type": "keyword"
          }
        }
      },
      "skillLevel": {
        "type": "keyword"
      },
      "sourceLink": {
        "type": "keyword"
      },
      "transportation": {
        "type": "keyword"
      }
    }
  }
}