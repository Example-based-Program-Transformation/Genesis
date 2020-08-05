// Copyright (C) 2016 Fan Long, Peter Amidon, Martin Rianrd and MIT CSAIL 
// Genesis (A successor of Prophet for Java Programs)
// 
// This file is part of Genesis.
// 
// Genesis is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 2 of the License, or
// (at your option) any later version.
// 
// Genesis is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with Genesis.  If not, see <http://www.gnu.org/licenses/>.
package genesis;

import java.util.ArrayList;
import java.util.List;

import genesis.infrastructure.UntarDir;
import genesis.node.MyCtNode;
import spoon.Launcher;
import spoon.reflect.code.CtBlock;
import spoon.reflect.code.CtExpression;
import spoon.reflect.code.CtFor;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.code.CtLiteral;
import spoon.reflect.code.CtLoop;
import spoon.reflect.code.CtStatement;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.declaration.CtPackage;
import spoon.reflect.declaration.CtType;
import spoon.reflect.factory.Factory;
import spoon.reflect.reference.CtExecutableReference;

public class TestSnippetParser {
	Launcher l;
	CtBlock<?> parentBlock;
	CtPackage rootPack;
	ArrayList<CtStatement> snippet;
	ArrayList<Object> startArgs;

	public TestSnippetParser(String path) {
		// We are going to use spoon to parse the jar file
		l = new Launcher();
		UntarDir tmpDir = new UntarDir(path);
		String tmpPath = tmpDir.untar();

		String[] spoonargs = {"-i", "", "--output-type", "nooutput", "-o", "/tmp/spooned", "--source-classpath", ""};
		spoonargs[1] = tmpPath + "/src/Basic.java";
		spoonargs[7] = tmpPath + "/src";
		l.run(spoonargs);
		tmpDir.clean();
		tmpDir = null;

		Factory f = l.getFactory();
		CtPackage p = f.Package().getRootPackage();
		rootPack = p;
		CtType<?> rootT = null;
		// This will only work for test cases, because we assume simple package structure!
		for (CtPackage p1 : p.getPackages()) {
			for (CtType<?> t : p1.getTypes())
				if (t.isTopLevel()) {
					rootT = t;
					break;
				}
			if (rootT != null) break;
		}
		snippet = null;
		startArgs = null;
		if (rootT == null) return;
		List<CtMethod<?>> lm = rootT.getMethodsByName("test");
		if (lm.size() == 0) return;
		CtMethod<?> m = lm.get(0);
		parentBlock = m.getBody();
		List<CtStatement> stmts = parentBlock.getStatements();
		snippet = new ArrayList<CtStatement>();
		startArgs = new ArrayList<Object>();
		processStatements(stmts);
	}

	private boolean processStatements(
			List<CtStatement> stmts) {
		boolean inside = false;
		boolean ret = false;
		for (CtStatement s : stmts) {
			if (s instanceof CtInvocation) {
				CtInvocation<?> invo = (CtInvocation<?>) s;
				CtExecutableReference<?> ref = invo.getExecutable();
				if (ref.getSimpleName().equals("snippetBegin")) {
					List<CtExpression<?>> args = invo.getArguments();
					for (CtExpression<?> a : args) {
						if (a instanceof CtLiteral) {
							CtLiteral<?> lit = (CtLiteral<?>) a;
							startArgs.add(lit.getValue());
						}
					}
					ret = true;
					inside = true;
					continue;
				}
				else if (ref.getSimpleName().equals("snippetEnd"))
					inside = false;
			}
			else if (!inside && snippet.size() == 0 && s instanceof CtLoop) {
				CtLoop loopEle = (CtLoop) s;
				CtStatement b = loopEle.getBody();
				if (b instanceof CtBlock) {
					ret = processStatements(((CtBlock<?>) b).getStatements());
					if (ret) {
						parentBlock = (CtBlock<?>) b;
						return ret;
					}
				}
			}
			// Just to handle for case	
			if (inside) snippet.add(s);
		}
		return ret;
	}

	public MyCtNode getCtNode() {
		return new MyCtNode(snippet, false, parentBlock);
	}

	public MyCtNode getRootPackage() {
		return new MyCtNode(rootPack, false);
	}
	
	// The startArg is the literal args inside the snippetBegin(args).
	// It is used to specify additional information for the test case
	public ArrayList<Object> getStartArgs() {
		return startArgs;
	}

	public Factory getFactory() {
		return l.getFactory();
	}
}
