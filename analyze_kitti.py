#!/usr/bin/env python3
# KITTIのCAR_3D_R40の各難易度ごとに10m刻みでインスタンス数をカウントするスクリプト
import os
import glob
import math

def get_bucket(distance):
    try:
        d = float(distance)
        if d >= 80:
            return ">80m"
        else:
            bucket_min = int(d // 10) * 10
            bucket_max = bucket_min + 10
            return f"{bucket_min}-{bucket_max}m"
    except:
        return None

def get_difficulty(bbox_height, occlusion, truncation):
    try:
        bbox_height = float(bbox_height)
        truncation = float(truncation)
        occlusion = int(occlusion)
    except:
        return None
    if bbox_height >= 40 and occlusion == 0 and truncation <= 0.15:
        return "easy"
    if bbox_height >= 25 and occlusion == 1 and truncation <= 0.30:
        return "moderate"
    if bbox_height >= 25 and occlusion == 2 and truncation <= 0.50:
        return "hard"
    return None

def parse_labels(label_file):
    objects = []
    with open(label_file, 'r') as f:
        for line in f:
            fields = line.strip().split()
            if len(fields) < 15:
                continue
            obj_type = fields[0]
            if obj_type != "Car":
                continue
            truncation = fields[1]
            occlusion = fields[2]
            try:
                bbox_top = float(fields[5])
                bbox_bottom = float(fields[7])
            except:
                continue
            bbox_height = bbox_bottom - bbox_top
            # Location: index 11: x, 12: y, 13: z
            try:
                x = float(fields[11])
                y = float(fields[12])
                z = float(fields[13])
                distance = math.sqrt(x*x + y*y + z*z)
            except:
                continue
            difficulty = get_difficulty(bbox_height, occlusion, truncation)
            if difficulty is None:
                continue
            bucket = get_bucket(distance)
            if bucket is None:
                continue
            objects.append((bucket, difficulty))
    return objects

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Count KITTI Car_3d objects by difficulty and distance bucket")
    parser.add_argument("--val_file", type=str, required=True, help="Path to val.txt file")
    parser.add_argument("--label_dir", type=str, required=True, help="Path to KITTI label directory")
    args = parser.parse_args()
    # Read validation set image IDs from provided file
    val_ids = set()
    with open(args.val_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                val_ids.add(line)
                
    label_files = glob.glob(os.path.join(args.label_dir, "*.txt"))
    
    counts_train = {}
    counts_val = {}
    
    for label_file in label_files:
        base = os.path.basename(label_file)
        file_id = os.path.splitext(base)[0]
        is_val = file_id in val_ids
        objs = parse_labels(label_file)
        for bucket, difficulty in objs:
            # Count only Car_3d keys with _R40 suffix
            key = f"Car_3d_{bucket}_{difficulty}_R40"
            if is_val:
                counts_val[key] = counts_val.get(key, 0) + 1
            else:
                counts_train[key] = counts_train.get(key, 0) + 1
                
    def print_grouped_counts(counts, set_name):
        print(f"{set_name} Set Counts:")
        difficulties = ["easy", "moderate", "hard"]
        # Group counts by difficulty and bucket.
        grouped = {diff: {} for diff in difficulties}
        for key, count in counts.items():
            # Expected format: Car_3d_{bucket}_{difficulty}_R40
            parts = key.split("_")
            if len(parts) < 5:
                continue
            bucket = parts[2]
            difficulty = parts[3]
            if difficulty in difficulties:
                grouped[difficulty][bucket] = grouped[difficulty].get(bucket, 0) + count
        def bucket_key(bucket):
            try:
                return int(bucket.split("-")[0])
            except:
                return 9999
        for diff in difficulties:
            print(f"  {diff.capitalize()}:")
            for bucket in sorted(grouped[diff].keys(), key=bucket_key):
                print(f"    {bucket}: {grouped[diff][bucket]}")
    
    print_grouped_counts(counts_train, "Train")
    print_grouped_counts(counts_val, "Val")
    
if __name__ == "__main__":
    main()
