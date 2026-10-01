// Cart Service — MongoDB collection setup
// Database: cart_service_db
// Run with: mongosh cart_service_db mongo_init.js

db = db.getSiblingDB("cart_service_db");

db.createCollection("carts", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id", "items", "status", "created_at", "updated_at"],
      properties: {
        user_id: { bsonType: "string" },
        status: { enum: ["ACTIVE", "CHECKED_OUT", "ABANDONED"] },
        items: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["product_id", "name_snapshot", "price_snapshot", "quantity"],
            properties: {
              product_id: { bsonType: "string" },
              name_snapshot: { bsonType: "string" },
              price_snapshot: { bsonType: "decimal" },
              quantity: { bsonType: "int", minimum: 1 },
              added_at: { bsonType: "date" },
            },
          },
        },
        created_at: { bsonType: "date" },
        updated_at: { bsonType: "date" },
      },
    },
  },
});

// One cart document per user — lookups are always by user_id.
db.carts.createIndex({ user_id: 1 }, { unique: true });

// Supports an abandoned-cart cleanup/reminder job filtering by status and age.
db.carts.createIndex({ status: 1, updated_at: 1 });
