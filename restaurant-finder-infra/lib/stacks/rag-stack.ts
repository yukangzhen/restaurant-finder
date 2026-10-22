import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3vectors from "aws-cdk-lib/aws-s3vectors";
import { Construct } from "constructs";
import { BaseStackProps } from "../types";

/** Retained, private document corpus and a dedicated Titan V2 index. */
export class RagStack extends cdk.Stack {
  readonly documentBucket: s3.Bucket;
  readonly vectorBucket: s3vectors.CfnVectorBucket;
  readonly vectorIndex: s3vectors.CfnIndex;

  constructor(scope: Construct, id: string, props: BaseStackProps) {
    super(scope, id, props);
    this.documentBucket = new s3.Bucket(this, "DocumentBucket", {
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
    this.vectorBucket = new s3vectors.CfnVectorBucket(this, "VectorBucket", {
      vectorBucketName: `${props.appName.toLowerCase()}-rag-${this.account}-${this.region}`,
      encryptionConfiguration: { sseType: "AES256" },
    });
    this.vectorBucket.applyRemovalPolicy(cdk.RemovalPolicy.RETAIN);
    this.vectorIndex = new s3vectors.CfnIndex(this, "DocumentIndex", {
      vectorBucketArn: this.vectorBucket.attrVectorBucketArn,
      indexName: "documents-titan-v2-512",
      dataType: "float32",
      dimension: 512,
      distanceMetric: "cosine",
      encryptionConfiguration: { sseType: "AES256" },
    });
    this.vectorIndex.applyRemovalPolicy(cdk.RemovalPolicy.RETAIN);
    new cdk.CfnOutput(this, "DocumentBucketName", { value: this.documentBucket.bucketName });
    new cdk.CfnOutput(this, "VectorBucketArn", { value: this.vectorBucket.attrVectorBucketArn });
    new cdk.CfnOutput(this, "VectorIndexArn", { value: this.vectorIndex.attrIndexArn });
    new cdk.CfnOutput(this, "ActiveManifestKey", { value: "rag/active.json" });
  }
}
