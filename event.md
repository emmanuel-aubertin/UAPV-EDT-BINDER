# Event API documentation

TODO: Write a quick intro

## Create an Event

This endpoint allows you to create a new event in the system. To create an event, you must provide details such as the start time, end time, title, memo, type, teacher code, classroom code, and promo code.

### HTTP Request

`POST /event/create`

### Headers

- `Content-Type: application/json`
- `Authorization: Bearer <your_access_token>`

### Request Body

| Field           | Type   | Description                               |
|-----------------|--------|-------------------------------------------|
| `start`         | String | Start time of the event (ISO 8601 format) |
| `end`           | String | End time of the event (ISO 8601 format)   |
| `title`         | String | Title of the event                        |
| `memo`          | String | Additional notes for the event            |
| `type`          | String | Type of the event                         |
| `teacher_code`  | String | Unique identifier for the teacher         |
| `classroom_code`| String | Unique identifier for the classroom       |
| `promo_code`    | String | Promotion code associated with the event  |

### cURL Example

```bash
curl --location '127.0.0.1:5000/event/create' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer XXX' \
--data '{
  "start": "2023-11-11T11:00:00+00:00",
  "end": "2023-11-11T11:30:00+00:00",
  "title": "Test de résa",
  "memo": "réunion projet",
  "type": "Pro",
  "teacher_code": "9882",
  "classroom_code": "AGR_A016",
  "promo_code": "2-L3IN"
}'
```

### Response

The response will include details of the created event along with a unique event ID.

#### Example Success Response

```json
{
    "event_code": "de8583b7",
    "message": "Event created successfully"
}
```

#### Example Error Response

```json
{
    "error": "Teacher not avaible"
}
```
---

## Get Events by Teacher

This endpoint retrieves all events associated with a specific teacher. It requires the teacher's unique code and an authorization token.

### HTTP Request

`GET /event/get/teacher/{TEACHER_CODE}`

### Headers

- `Authorization: Bearer {YOUR_TOKEN}`

### URL Parameters

| Parameter      | Type   | Description                               |
|----------------|--------|-------------------------------------------|
| `TEACHER_CODE` | String | Unique identifier for the teacher whose events you want to retrieve |

### cURL Example

```bash
curl --location 'http://127.0.0.1:5000/event/get/teacher/{TEACHER_CODE}' \
--header 'Authorization: Bearer {YOUR_TOKEN}'
```

### Response

The response will include an array of events associated with the specified teacher. Each event object in the array contains details such as the event code, start and end times, title, memo, type, and potentially classroom and promo codes.

#### Example Success Response

```json
{
    "results": [
        {
            "code": null,
            "end": "2023-10-11T11:30:00+00:00",
            "favori": "",
            "memo": null,
            "start": "2023-10-11T11:00:00+00:00",
            "title": "Matière : CMI 1 : INITIATION RECHERCHE\nEnseignant : XXXXXX\nTD : L1 S1, MI - I 6 (CMI)\nSalle : S8 = C 030\nType : TD\nMémo : CMI UNIQUEMENT\n",
            "type": "TD"
        },
        ...
        {
            "classroom_code": "AGR_A016",
            "code": "de8583b7",
            "end": "2023-11-11T11:30:00+00:00",
            "memo": "réunion projet",
            "promo_code": "2-L3IN",
            "start": "2023-11-11T11:00:00+00:00",
            "teacher_code": "9882",
            "title": "Test de résa",
            "type": "Pro"
        }
    ]
}
```

#### Notes

- The `code` field may be `null` for some events if they are fetched from external sources or if the event code is not applicable.
- The response includes various details about each event, potentially including custom memos, type designations (e.g., "TD" for teaching duties, "Pro" for professional events), and identifiers for related entities like classrooms or promotions.
- The response format and content might vary based on the specific implementation and data availability.