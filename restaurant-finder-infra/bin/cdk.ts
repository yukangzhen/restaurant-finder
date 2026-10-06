#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { BaseStackProps } from "../lib/types";
import { EcrStack, AgentCoreStack } from "../lib/stacks";

const app = new cdk.App();

// Override image URI via context variable:
//   npx cdk deploy --all -c imageUri=<account>.dkr.ecr.<region>.amazonaws.com/restaurantfinder-agent:<tag>
const existingImageUri = app.node.tryGetContext("imageUri") as
  | string
  | undefined;

const deploymentProps: BaseStackProps = {
  appName: "restaurantFinder",
  // Keep project resources in us-east-2 even when the AWS CLI profile defaults elsewhere.
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: "us-east-2",
  },
};
// ECR repository is always created as infrastructure
const ecrStack = new EcrStack(
  app,
  `restaurantFinder-EcrStack`,
  deploymentProps,
);

// Determine image URI:
// - If provided via context (-c imageUri=...), use that specific image
// - Otherwise, default to the ECR repo with :latest tag
const imageUri = existingImageUri || `${ecrStack.repositoryUri}:latest`;

if (existingImageUri) {
  console.log(`Using provided image URI: ${existingImageUri}`);
} else {
  console.log(`Using default ECR image URI: ${imageUri}`);
}

const agentCoreStack = new AgentCoreStack(
  app,
  `restaurantFinder-AgentCoreStack`,
  {
    ...deploymentProps,
    imageUri: imageUri,
  },
);

agentCoreStack.addDependency(ecrStack);
