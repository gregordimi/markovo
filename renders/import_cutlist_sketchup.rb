# ==============================================================================
# MARKOVO KITCHEN — IMPORT CUTLIST CSV INTO SKETCHUP
# ==============================================================================
# How to run in SketchUp:
#   1. Open SketchUp
#   2. Go to: Window > Ruby Console (or Extensions > Developer > Ruby Console)
#   3. Paste the following line and press Enter:
#        load '/Users/gdimitrov/projects/markovo/renders/import_cutlist_sketchup.rb'
# ==============================================================================

require 'csv'

csv_path = File.expand_path("kitchen_cutlist.csv", __dir__)

unless File.exist?(csv_path)
  UI.messagebox("Could not find #{csv_path}")
  return
end

model = Sketchup.active_model
model.start_operation("Import Kitchen Cutlist", true)

x_cursor = 0.mm
y_cursor = 0.mm
row_max_w = 0.mm

count = 0

CSV.foreach(csv_path, headers: true) do |row|
  name = row["Part Name"]
  cabinet = row["Cabinet"]
  l = row["Length (mm)"].to_f.mm
  w = row["Width (mm)"].to_f.mm
  t = row["Thickness (mm)"].to_f.mm
  qty = row["Qty"].to_i
  mat = row["Material"]

  qty.times do |i|
    grp = model.active_entities.add_group
    grp.name = qty > 1 ? "#{name}_#{i+1}" : name

    # Set attributes for OpenCutList / CutList Bridge if present
    grp.set_attribute("OpenCutList", "material", mat)
    grp.set_attribute("dynamic_attributes", "description", cabinet)

    pts = [
      [x_cursor, y_cursor, 0],
      [x_cursor + l, y_cursor, 0],
      [x_cursor + l, y_cursor + w, 0],
      [x_cursor, y_cursor + w, 0]
    ]

    face = grp.entities.add_face(pts)
    face.pushpull(-t)

    x_cursor += l + 40.mm
    row_max_w = [row_max_w, w].max

    if x_cursor > 3200.mm
      x_cursor = 0.mm
      y_cursor += row_max_w + 60.mm
      row_max_w = 0.mm
    end

    count += 1
  end
end

model.commit_operation
puts "Successfully imported #{count} panels into SketchUp from #{csv_path}!"

