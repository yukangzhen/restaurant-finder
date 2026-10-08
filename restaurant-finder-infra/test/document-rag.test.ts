import * as cdk from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { RagStack, AgentCoreStack } from "../lib/stacks";

const env = { account: "123456789012", region: "us-east-2" };

test("corpus bucket is private, versioned, TLS-only and retained", () => {
  const stack = new RagStack(new cdk.App(), "Rag", { appName: "restaurantFinder", env });
  const template = Template.fromStack(stack);
  template.hasResourceProperties("AWS::S3::Bucket", {
    VersioningConfiguration: { Status: "Enabled" },
    BucketEncryption: { ServerSideEncryptionConfiguration: [{ ServerSideEncryptionByDefault: { SSEAlgorithm: "AES256" } }] },
    PublicAccessBlockConfiguration: { BlockPublicAcls: true, BlockPublicPolicy: true, IgnorePublicAcls: true, RestrictPublicBuckets: true },
  });
  template.hasResource("AWS::S3::Bucket", { DeletionPolicy: "Retain", UpdateReplacePolicy: "Retain" });
  const policies = Object.values(template.findResources("AWS::S3::BucketPolicy")) as any[];
  expect(policies[0].Properties.PolicyDocument.Statement).toEqual(expect.arrayContaining([
    expect.objectContaining({ Effect: "Deny", Condition: { Bool: { "aws:SecureTransport": "false" } } }),
  ]));
});

test("index is retained float32/512/cosine without unsupported indexMode", () => {
  const stack = new RagStack(new cdk.App(), "Rag", { appName: "restaurantFinder", env });
  const template = Template.fromStack(stack);
  template.hasResourceProperties("AWS::S3Vectors::Index", { Dimension: 512, DataType: "float32", DistanceMetric: "cosine" });
  template.hasResource("AWS::S3Vectors::Index", { DeletionPolicy: "Retain", UpdateReplacePolicy: "Retain" });
  expect(JSON.stringify(template.toJSON())).not.toContain("IndexMode");
});

test("runtime has exact RAG read permissions and fixed environment", () => {
  const stack = new AgentCoreStack(new cdk.App(), "Agent", { appName: "restaurantFinder", env, imageUri: "demo:image",
    ragDocumentBucketName: "demo-corpus", ragDocumentBucketArn: "arn:aws:s3:::demo-corpus",
    ragVectorIndexArn: "arn:aws:s3vectors:us-east-2:123456789012:bucket/demo/index/documents" });
  const template = Template.fromStack(stack);
  const roles = Object.values(template.findResources("AWS::IAM::Role")) as any[];
  const statements = roles.flatMap(r => (r.Properties.Policies || []).flatMap((p: any) => p.PolicyDocument.Statement));
  const vector = statements.find(s => s.Sid === "DocumentRagVectorRead");
  expect(vector.Action.sort()).toEqual(["s3vectors:GetIndex", "s3vectors:GetVectors", "s3vectors:QueryVectors"]);
  expect(vector.Resource).toBe("arn:aws:s3vectors:us-east-2:123456789012:bucket/demo/index/documents");
  const objects = statements.find(s => s.Sid === "DocumentRagObjectRead");
  expect(objects.Action).toBe("s3:GetObject");
  expect(objects.Resource).toHaveLength(3);
  expect(JSON.stringify(objects)).not.toContain("embedding-cache");
  expect(statements.find(s => s.Sid === "DocumentRagEmbeddingInvocation").Resource).toBe("arn:aws:bedrock:us-east-2::foundation-model/amazon.titan-embed-text-v2:0");
  const runtime = Object.values(template.findResources("AWS::BedrockAgentCore::Runtime")) as any[];
  expect(runtime[0].Properties.EnvironmentVariables.DOCUMENT_RAG_ENABLED).toBe("true");
  expect(runtime[0].Properties.EnvironmentVariables.RAG_EMBEDDING_DIMENSIONS).toBe("512");
  expect(statements.find(s => s.Sid === "S3BucketAccess")).toBeUndefined();
});
