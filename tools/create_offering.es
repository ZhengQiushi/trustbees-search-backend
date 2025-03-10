PUT /offerings_v2
{
  "mappings": {
    "properties": {
      "latePickup": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "RSVP": {
        "type": "text"
      },
      "RSVPDeadline": {
        "type": "date"
      },
      "activity": {
        "type": "text",
        "copy_to": [
          "activityEmbeddings"
        ]
      },
      "activityCategory": {
        "type": "text",
        "copy_to": [
          "activityCategoryEmbeddings"
        ]
      },
      "activityCategoryEmbeddings": {
        "type": "semantic_text",
        "inference_id": "google_ai_studio_completion",
        "model_settings": {
          "task_type": "text_embedding",
          "dimensions": 768,
          "similarity": "dot_product",
          "element_type": "float"
        }
      },
      "activityEmbeddings": {
        "type": "semantic_text",
        "inference_id": "google_ai_studio_completion",
        "model_settings": {
          "task_type": "text_embedding",
          "dimensions": 768,
          "similarity": "dot_product",
          "element_type": "float"
        }
      },
      "ageGroup": {
        "type": "integer_range"
      },
      "businessFullName": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "businessFullNameEmbeddings": {
        "type": "semantic_text",
        "inference_id": "google_ai_studio_completion",
        "model_settings": {
          "task_type": "text_embedding",
          "dimensions": 768,
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
      "earlyDropOff": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      },
      "facility": {
        "type": "keyword"
      },
      "hyperlink": {
        "type": "text"
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
      "offeringInsightSummary": {
        "type": "text",
        "copy_to": [
          "offeringInsightSummaryEmbeddings"
        ]
      },
      "offeringInsightSummaryEmbeddings": {
        "type": "semantic_text",
        "inference_id": "google_ai_studio_completion",
        "model_settings": {
          "task_type": "text_embedding",
          "dimensions": 768,
          "similarity": "dot_product",
          "element_type": "float"
        }
      },
      "offeringName": {
        "type": "text",
        "copy_to": [
          "offeringNameEmbeddings"
        ]
      },
      "offeringNameEmbeddings": {
        "type": "semantic_text",
        "inference_id": "google_ai_studio_completion",
        "model_settings": {
          "task_type": "text_embedding",
          "dimensions": 768,
          "similarity": "dot_product",
          "element_type": "float"
        }
      },
      "offeringType": {
        "type": "keyword"
      },
      "pricing": {
        "type": "text"
      },
      "schedule": {
        "type": "nested",
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
      "scheduleSummary": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
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